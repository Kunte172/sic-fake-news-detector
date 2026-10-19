from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.orm import Session

import os
from sqlalchemy.exc import IntegrityError
from . import database, models
from .auth import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from .inference import Predictor

class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=80, max_length=50_000)

class AnalyzeResponse(BaseModel):
    label: str
    score: float
    model_version: str

class UserRegisterRequest(BaseModel):
    email: EmailStr

    password: str = Field(min_length=6, max_length=72, description="Mật khẩu từ 6-72 ký tự")

    @field_validator("password")
    @classmethod
    def check_bytes(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Mật khẩu vượt quá 72 byte")
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

@lru_cache
def predictor() -> Predictor:
    return Predictor()

app = FastAPI(title="SIC Fake News Lens", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

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
def analyze(body: AnalyzeRequest) -> AnalyzeResponse:
    if not predictor().ready:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Train a baseline and set MODEL_PATH.",
        )
    label, score = predictor().predict(body.text)
    return AnalyzeResponse(label=label, score=score, model_version="baseline-v0")

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