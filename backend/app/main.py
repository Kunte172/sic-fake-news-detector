from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field

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
    password: str = Field(min_length=6, description="Mật khẩu tối thiểu 6 ký tự")
    role: str = Field(default="USER", description="Quyền: USER hoặc ADMIN")


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

users_db: dict[str, dict] = {
    "admin@example.com": {
        "email": "admin@example.com",
        "hashed_password": get_password_hash("Admin@123456"),
        "role": "ADMIN",
    }
}

security = HTTPBearer()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> dict:
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email = payload.get("sub")
    if not email or email not in users_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Người dùng không tồn tại trong hệ thống",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return users_db[email]


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
def register(body: UserRegisterRequest) -> UserResponse:
    if body.email in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã được đăng ký",
        )
    role = body.role.upper()
    if role not in ("USER", "ADMIN"):
        role = "USER"

    hashed_pw = get_password_hash(body.password)
    users_db[body.email] = {
        "email": body.email,
        "hashed_password": hashed_pw,
        "role": role,
    }
    return UserResponse(email=body.email, role=role)


@app.post("/api/v1/auth/login", response_model=TokenResponse)
def login(body: UserLoginRequest) -> TokenResponse:
    user = users_db.get(body.email)
    if not user or not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác",
        )

    token = create_access_token(data={"sub": user["email"], "role": user["role"]})
    return TokenResponse(access_token=token, token_type="bearer", role=user["role"])


@app.get("/api/v1/auth/me", response_model=UserResponse)
def get_me(current_user: Annotated[dict, Depends(get_current_user)]) -> UserResponse:
    return UserResponse(email=current_user["email"], role=current_user["role"])