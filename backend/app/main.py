from datetime import datetime, timezone
from functools import lru_cache
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from .auth import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from .database import Base, engine, get_db
from .inference import Predictor
from . import models

Base.metadata.create_all(bind=engine)



class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=80, max_length=50_000)


class AnalyzeResponse(BaseModel):
    id: Optional[int] = None
    label: str
    score: float
    model_version: str


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, description="Mật khẩu tối thiểu 6 ký tự")
    role: str = Field(default="USER", description="USER hoặc ADMIN")


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class UserResponse(BaseModel):
    email: str
    role: str


class FeedbackCreateRequest(BaseModel):
    agree: bool
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: int
    analysis_id: int
    agree: bool
    comment: Optional[str] = None

    class Config:
        from_attributes = True


class AnalysisHistoryItem(BaseModel):
    id: int
    input_type: str
    content_preview: Optional[str]
    label: str
    score: float
    model_version: str
    created_at: datetime
    feedback: Optional[FeedbackResponse] = None

    class Config:
        from_attributes = True


class PaginatedAnalysesResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[AnalysisHistoryItem]



@lru_cache
def predictor() -> Predictor:
    return Predictor()


app = FastAPI(title="SIC Fake News Lens", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)



def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> models.User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Yêu cầu đăng nhập",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email = payload.get("sub")
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Người dùng không tồn tại",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_admin(
    current_user: Annotated[models.User, Depends(get_current_user)]
) -> models.User:
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ quản trị viên mới có quyền truy cập",
        )
    return current_user


@app.on_event("startup")
def init_admin_user():
    db = next(get_db())
    try:
        admin_email = "admin@example.com"
        if not db.query(models.User).filter(models.User.email == admin_email).first():
            admin_user = models.User(
                email=admin_email,
                hashed_password=get_password_hash("Admin@123456"),
                role="ADMIN",
            )
            db.add(admin_user)
            db.commit()
    finally:
        db.close()



@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model_loaded": predictor().ready}


@app.post("/api/v1/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(body: UserRegisterRequest, db: Annotated[Session, Depends(get_db)]) -> UserResponse:
    if db.query(models.User).filter(models.User.email == body.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email đã được đăng ký")
    role = body.role.upper() if body.role.upper() in ("USER", "ADMIN") else "USER"
    new_user = models.User(
        email=body.email,
        hashed_password=get_password_hash(body.password),
        role=role,
    )
    db.add(new_user)
    db.commit()
    return UserResponse(email=new_user.email, role=new_user.role)


@app.post("/api/v1/auth/login", response_model=TokenResponse)
def login(body: UserLoginRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email hoặc mật khẩu không chính xác")
    token = create_access_token(data={"sub": user.email, "role": user.role})
    return TokenResponse(access_token=token, token_type="bearer", role=user.role)


@app.get("/api/v1/auth/me", response_model=UserResponse)
def get_me(current_user: Annotated[models.User, Depends(get_current_user)]) -> UserResponse:
    return UserResponse(email=current_user.email, role=current_user.role)


@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
def analyze(
    body: AnalyzeRequest,
    db: Annotated[Session, Depends(get_db)],
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> AnalyzeResponse:
    if not predictor().ready:
        raise HTTPException(status_code=503, detail="Model not loaded. Train a baseline and set MODEL_PATH.")
    label, score = predictor().predict(body.text)
    analysis_id = None

    if credentials:
        payload = decode_access_token(credentials.credentials)
        if payload:
            user = db.query(models.User).filter(models.User.email == payload.get("sub")).first()
            if user:
                record = models.Analysis(
                    user_id=user.id,
                    input_type="text",
                    content_preview=body.text[:120].strip() + ("..." if len(body.text) > 120 else ""),
                    label=label,
                    score=score,
                    model_version="baseline-v0",
                )
                db.add(record)
                db.commit()
                db.refresh(record)
                analysis_id = record.id

    return AnalyzeResponse(id=analysis_id, label=label, score=score, model_version="baseline-v0")


@app.get("/api/v1/analyses", response_model=PaginatedAnalysesResponse)
def get_user_analyses(
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
) -> PaginatedAnalysesResponse:
    query = db.query(models.Analysis).filter(models.Analysis.user_id == current_user.id)
    total = query.count()
    items = query.order_by(models.Analysis.created_at.desc()).offset(offset).limit(limit).all()
    return PaginatedAnalysesResponse(total=total, limit=limit, offset=offset, items=items)


@app.post("/api/v1/analyses/{analysis_id}/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    analysis_id: int,
    body: FeedbackCreateRequest,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FeedbackResponse:
    analysis = db.query(models.Analysis).filter(
        models.Analysis.id == analysis_id,
        models.Analysis.user_id == current_user.id
    ).first()
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy lượt phân tích của bạn")

    existing_feedback = db.query(models.Feedback).filter(models.Feedback.analysis_id == analysis_id).first()
    if existing_feedback:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lượt phân tích này đã được gửi phản hồi")

    feedback = models.Feedback(
        analysis_id=analysis_id,
        user_id=current_user.id,
        agree=body.agree,
        comment=body.comment,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


@app.get("/api/v1/admin/summary")
def get_admin_summary(
    _: Annotated[models.User, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    total_users = db.query(models.User).count()
    total_analyses = db.query(models.Analysis).count()
    total_feedbacks = db.query(models.Feedback).count()
    disputed_count = db.query(models.Feedback).filter(models.Feedback.agree == False).count()
    return {
        "total_users": total_users,
        "total_analyses": total_analyses,
        "total_feedbacks": total_feedbacks,
        "disputed_feedbacks": disputed_count,
    }


@app.get("/api/v1/admin/disputed")
def get_admin_disputed(
    _: Annotated[models.User, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
) -> dict:
    query = (
        db.query(models.Feedback)
        .filter(models.Feedback.agree == False)
        .order_by(models.Feedback.created_at.desc())
    )
    total = query.count()
    feedbacks = query.offset(offset).limit(limit).all()
    items = []
    for fb in feedbacks:
        items.append({
            "feedback_id": fb.id,
            "analysis_id": fb.analysis_id,
            "comment": fb.comment,
            "label": fb.analysis.label if fb.analysis else None,
            "score": fb.analysis.score if fb.analysis else None,
            "content_preview": fb.analysis.content_preview if fb.analysis else None,
            "created_at": fb.created_at,
        })
    return {"total": total, "limit": limit, "offset": offset, "items": items}