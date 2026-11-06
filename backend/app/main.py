from functools import lru_cache
from typing import Annotated
from datetime import datetime
from datetime import timedelta, timezone
import hashlib
import secrets
import smtplib
from email.message import EmailMessage
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from sqlalchemy.orm import Session, joinedload

import os
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from . import database, models
from .auth import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from .inference import Predictor
from .url_extraction import UrlError, fetch_article
from .fact_check import verify_claims

class AnalyzeRequest(BaseModel):
    text: str | None = Field(default=None, min_length=80, max_length=50_000)
    url: str | None = Field(default=None, min_length=1, max_length=2048)

    @model_validator(mode="after")
    def exactly_one_input(self):
        if (self.text is None) == (self.url is None):
            raise ValueError("Provide exactly one of text or url")
        return self

class AnalyzeResponse(BaseModel):
    id: int | None = None
    label: str
    score: float
    model_version: str
    score_kind: str = "model_probability"
    explanation: dict | None = None
    review_status: str = "NEEDS_REVIEW"
    decision: str = "NEEDS_REVIEW"
    source_domain: str | None = None
    source_scope: str
    review_reason: str
    verification: dict

class UserRegisterRequest(BaseModel):
    email: EmailStr

    password: str = Field(min_length=6, max_length=72, description="Mật khẩu từ 6-72 ký tự")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Mật khẩu vượt quá 72 byte")
        if not v[0].isupper() or not any(not char.isalnum() and not char.isspace() for char in v):
            raise ValueError("Mật khẩu phải bắt đầu bằng chữ hoa và có ít nhất một ký tự đặc biệt")
        return v

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=72)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str

class UserResponse(BaseModel):
    email: str
    role: str

class EmailCodeRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Mật khẩu vượt quá 72 byte")
        if not v[0].isupper() or not any(not char.isalnum() and not char.isspace() for char in v):
            raise ValueError("Mật khẩu phải bắt đầu bằng chữ hoa và có ít nhất một ký tự đặc biệt")
        return v

class VerifyEmailCodeRequest(EmailCodeRequest):
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")

class PasswordResetRequest(BaseModel):
    email: EmailStr

class VerifyResetCodeRequest(PasswordResetRequest):
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    password: str = Field(min_length=6, max_length=72)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Mật khẩu vượt quá 72 byte")
        if not v[0].isupper() or not any(not char.isalnum() and not char.isspace() for char in v):
            raise ValueError("Mật khẩu phải bắt đầu bằng chữ hoa và có ít nhất một ký tự đặc biệt")
        return v

class FeedbackRequest(BaseModel):
    agree: bool
    comment: str | None = Field(default=None, max_length=1000)

class FeedbackResponse(BaseModel):
    id: int
    analysis_id: int
    agree: bool
    comment: str | None

class AnalysisHistoryItem(BaseModel):
    id: int
    input_type: str
    content_preview: str
    label: str
    score: float
    model_version: str
    created_at: datetime
    feedback: FeedbackResponse | None

class PaginatedAnalyses(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[AnalysisHistoryItem]

class DisputedItem(BaseModel):
    feedback_id: int
    analysis_id: int
    comment: str | None
    label: str
    score: float
    content_preview: str
    model_version: str
    created_at: datetime

class PaginatedDisputed(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[DisputedItem]

@lru_cache
def predictor() -> Predictor:
    return Predictor()

app = FastAPI(title="SIC Fake News Lens", version="0.1.0")

def _send_code(email: str, code: str, purpose: str) -> None:
    host = os.getenv("SMTP_HOST")
    if not host:
        raise HTTPException(status_code=503, detail="Email chưa được cấu hình trên máy chủ")
    message = EmailMessage()
    message["Subject"] = "Mã xác minh SIC / Fake News Lens"
    message["From"] = os.getenv("SMTP_FROM", os.getenv("SMTP_USER", ""))
    message["To"] = email
    message.set_content(
        f"Mã xác minh của bạn là: {code}\n\n"
        f"Mã có hiệu lực trong 10 phút cho thao tác {purpose}."
    )
    try:
        with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=10) as server:
            server.starttls()
            server.login(
                os.getenv("SMTP_USER", ""),
                os.getenv("SMTP_PASSWORD", "").replace(" ", ""),
            )
            server.send_message(message)
    except (OSError, smtplib.SMTPException) as cause:
        raise HTTPException(status_code=503, detail="Không thể gửi email xác minh") from cause

def _code_hash(code: str) -> str:
    return hashlib.sha256(code.encode("ascii")).hexdigest()

def _new_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"

def _is_expired(expires_at: datetime) -> bool:
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at < datetime.now(timezone.utc)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "https://sic-fake-news-web.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)

def get_optional_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(optional_security)],
    db: Annotated[Session, Depends(database.get_db)],
) -> models.User | None:
    if not request.headers.get("Authorization"):
        return None
    if credentials is None:
        raise HTTPException(status_code=401, detail="Token không hợp lệ")
    payload = decode_access_token(credentials.credentials)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc đã hết hạn")
    user = db.query(models.User).filter(models.User.email == payload["sub"]).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Người dùng không tồn tại")
    return user

def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[Session, Depends(database.get_db)]
) -> models.User:
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không chứa thông tin",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Người dùng không tồn tại trong hệ thống",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def require_admin(
    current_user: Annotated[models.User, Depends(get_current_user)],
) -> models.User:
    if current_user.role != models.Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập chức năng này",
        )
    return current_user

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model_loaded": predictor().ready}

@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
def analyze(
    body: AnalyzeRequest,
    db: Annotated[Session, Depends(database.get_db)],
    current_user: Annotated[models.User | None, Depends(get_optional_user)],
) -> AnalyzeResponse:
    if not predictor().ready:
        raise HTTPException(
            status_code=503,
            detail=(
                "Model not loaded. "
                + (predictor().error or "Set MODEL_PATH to a trained artifact.")
            ),
        )
    try:
        article_text = fetch_article(body.url) if body.url is not None else body.text
    except UrlError as cause:
        raise HTTPException(status_code=cause.status_code, detail=cause.detail) from cause
    try:
        source_domain = urlparse(body.url).hostname.lower() if body.url else None
        prediction = predictor().analyze(article_text, source_domain=source_domain)
        prediction["verification"] = verify_claims(article_text)
    except ValueError as cause:
        raise HTTPException(status_code=422, detail=str(cause)) from cause
    analysis_id = None
    if current_user is not None:
        record = models.Analysis(
            user_id=current_user.id,
            input_type="url" if body.url is not None else "text",
            content_preview=article_text[:120],
            label=prediction["label"],
            score=prediction["score"],
            model_version=prediction["model_version"],
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        analysis_id = record.id
    return AnalyzeResponse(id=analysis_id, **prediction)

@app.get("/api/v1/analyses", response_model=PaginatedAnalyses)
def get_analyses(
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Annotated[Session, Depends(database.get_db)],
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
) -> PaginatedAnalyses:
    query = db.query(models.Analysis).filter(models.Analysis.user_id == current_user.id)
    total = query.count()
    records = (query.options(joinedload(models.Analysis.feedback))
               .order_by(models.Analysis.created_at.desc(), models.Analysis.id.desc())
               .offset(offset).limit(limit).all())
    items = [AnalysisHistoryItem(
        id=row.id, input_type=row.input_type, content_preview=row.content_preview,
        label=row.label, score=row.score, model_version=row.model_version,
        created_at=row.created_at,
        feedback=(FeedbackResponse(id=row.feedback.id, analysis_id=row.id,
                                   agree=row.feedback.agree, comment=row.feedback.comment)
                  if row.feedback else None),
    ) for row in records]
    return PaginatedAnalyses(total=total, limit=limit, offset=offset, items=items)

@app.post("/api/v1/analyses/{analysis_id}/feedback", response_model=FeedbackResponse, status_code=201)
def submit_feedback(
    analysis_id: int,
    body: FeedbackRequest,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Annotated[Session, Depends(database.get_db)],
) -> FeedbackResponse:
    analysis = db.query(models.Analysis).filter(
        models.Analysis.id == analysis_id, models.Analysis.user_id == current_user.id,
    ).first()
    if analysis is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy lượt phân tích")
    if db.query(models.Feedback.id).filter(models.Feedback.analysis_id == analysis_id).first():
        raise HTTPException(status_code=409, detail="Lượt phân tích đã có phản hồi")
    feedback = models.Feedback(
        analysis_id=analysis_id, user_id=current_user.id,
        agree=body.agree, comment=body.comment,
    )
    db.add(feedback)
    try:
        db.commit()
        db.refresh(feedback)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Lượt phân tích đã có phản hồi")
    return FeedbackResponse(id=feedback.id, analysis_id=analysis_id,
                            agree=feedback.agree, comment=feedback.comment)

@app.get("/api/v1/admin/summary")
def admin_summary(
    _: Annotated[models.User, Depends(require_admin)],
    db: Annotated[Session, Depends(database.get_db)],
) -> dict:
    return {
        "total_users": db.query(models.User).count(),
        "total_analyses": db.query(models.Analysis).count(),
        "total_feedbacks": db.query(models.Feedback).count(),
        "disputed_feedbacks": db.query(models.Feedback).filter(models.Feedback.agree.is_(False)).count(),
    }

@app.get("/api/v1/admin/disputed", response_model=PaginatedDisputed)
def admin_disputed(
    _: Annotated[models.User, Depends(require_admin)],
    db: Annotated[Session, Depends(database.get_db)],
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
) -> PaginatedDisputed:
    query = db.query(models.Feedback).filter(models.Feedback.agree.is_(False))
    total = query.count()
    records = (query.options(joinedload(models.Feedback.analysis))
               .order_by(models.Feedback.created_at.desc(), models.Feedback.id.desc())
               .offset(offset).limit(limit).all())
    items = [DisputedItem(
        feedback_id=fb.id, analysis_id=fb.analysis_id, comment=fb.comment,
        label=fb.analysis.label, score=fb.analysis.score,
        content_preview=fb.analysis.content_preview,
        model_version=fb.analysis.model_version, created_at=fb.created_at,
    ) for fb in records]
    return PaginatedDisputed(total=total, limit=limit, offset=offset, items=items)

@app.post(
    "/api/v1/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(body: UserRegisterRequest, db: Annotated[Session, Depends(database.get_db)]) -> UserResponse:
    email_lower = body.email.lower()
    
    existing_user = db.query(models.User).filter(models.User.email == email_lower).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã được đăng ký",
        )
    
    hashed_pw = get_password_hash(body.password)
    
    new_user = models.User(
        email=email_lower,
        hashed_password=hashed_pw,
        role=models.Role.USER, 
    )
    db.add(new_user)
    
    try:
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã được đăng ký",
        )
    
    return UserResponse(email=new_user.email, role=new_user.role.value)

@app.post("/api/v1/auth/register/request-code", status_code=202)
def request_registration_code(body: EmailCodeRequest, db: Annotated[Session, Depends(database.get_db)]) -> dict[str, str]:
    email = body.email.lower()
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status_code=400, detail="Email đã được đăng ký")
    code = _new_code()
    db.query(models.EmailCode).filter(
        models.EmailCode.email == email, models.EmailCode.purpose == "register"
    ).delete()
    db.add(models.EmailCode(
        email=email, purpose="register", code_hash=_code_hash(code),
        password_hash=get_password_hash(body.password),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    ))
    db.commit()
    _send_code(email, code, "đăng ký tài khoản")
    return {"message": "Mã xác minh đã được gửi đến email"}

@app.post("/api/v1/auth/register/verify", response_model=UserResponse, status_code=201)
def verify_registration_code(body: VerifyEmailCodeRequest, db: Annotated[Session, Depends(database.get_db)]) -> UserResponse:
    email = body.email.lower()
    record = (db.query(models.EmailCode)
              .filter(models.EmailCode.email == email, models.EmailCode.purpose == "register")
              .order_by(models.EmailCode.created_at.desc()).first())
    if not record or _is_expired(record.expires_at) or record.attempts >= 5:
        raise HTTPException(status_code=400, detail="Mã xác minh không hợp lệ hoặc đã hết hạn")
    if record.code_hash != _code_hash(body.code):
        record.attempts += 1
        db.commit()
        raise HTTPException(status_code=400, detail="Mã xác minh không đúng")
    user = models.User(email=email, hashed_password=record.password_hash, role=models.Role.USER)
    db.add(user)
    db.delete(record)
    try:
        db.commit()
    except IntegrityError as cause:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email đã được đăng ký") from cause
    return UserResponse(email=user.email, role=user.role.value)

@app.post("/api/v1/auth/password-reset/request-code", status_code=202)
def request_password_reset_code(body: PasswordResetRequest, db: Annotated[Session, Depends(database.get_db)]) -> dict[str, str]:
    email = body.email.lower()
    if not db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status_code=404, detail="Email chưa được đăng ký")
    code = _new_code()
    db.query(models.EmailCode).filter(
        models.EmailCode.email == email, models.EmailCode.purpose == "reset"
    ).delete()
    db.add(models.EmailCode(
        email=email, purpose="reset", code_hash=_code_hash(code),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    ))
    db.commit()
    _send_code(email, code, "đặt lại mật khẩu")
    return {"message": "Mã xác minh đã được gửi đến email"}

@app.post("/api/v1/auth/password-reset/verify", status_code=204)
def verify_password_reset_code(body: VerifyResetCodeRequest, db: Annotated[Session, Depends(database.get_db)]) -> None:
    email = body.email.lower()
    record = (db.query(models.EmailCode)
              .filter(models.EmailCode.email == email, models.EmailCode.purpose == "reset")
              .order_by(models.EmailCode.created_at.desc()).first())
    if not record or _is_expired(record.expires_at) or record.attempts >= 5:
        raise HTTPException(status_code=400, detail="Mã xác minh không hợp lệ hoặc đã hết hạn")
    if record.code_hash != _code_hash(body.code):
        record.attempts += 1
        db.commit()
        raise HTTPException(status_code=400, detail="Mã xác minh không đúng")
    user = db.query(models.User).filter(models.User.email == email).first()
    user.hashed_password = get_password_hash(body.password)
    db.delete(record)
    db.commit()

@app.post("/api/v1/auth/login", response_model=TokenResponse)
def login(body: UserLoginRequest, db: Annotated[Session, Depends(database.get_db)]) -> TokenResponse:
    email_lower = body.email.lower()
    
    user = db.query(models.User).filter(models.User.email == email_lower).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác",
        )

    token = create_access_token(data={"sub": user.email, "role": user.role.value})
    return TokenResponse(access_token=token, token_type="bearer", role=user.role.value)

@app.get("/api/v1/auth/me", response_model=UserResponse)
def get_me(current_user: Annotated[models.User, Depends(get_current_user)]) -> UserResponse:
    return UserResponse(email=current_user.email, role=current_user.role.value)

@app.on_event("startup")
def init_admin_user():
    admin_email = os.environ.get("ADMIN_EMAIL")
    admin_password = os.environ.get("ADMIN_PASSWORD")
    
    if not admin_email or not admin_password:
        return

    db = next(database.get_db())
    try:
        admin_email_lower = admin_email.lower()
        admin_user = db.query(models.User).filter(models.User.email == admin_email_lower).first()
        if not admin_user:
            hashed_pw = get_password_hash(admin_password)
            new_admin = models.User(email=admin_email_lower, hashed_password=hashed_pw, role=models.Role.ADMIN)
            db.add(new_admin)
            db.commit()
    finally:
        db.close()
