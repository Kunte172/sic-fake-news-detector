from functools import lru_cache

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .inference import Predictor


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=80, max_length=50_000)


class AnalyzeResponse(BaseModel):
    label: str
    score: float
    model_version: str


@lru_cache
def predictor() -> Predictor:
    return Predictor()


app = FastAPI(title="SIC Fake News Lens", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model_loaded": predictor().ready}


@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
def analyze(body: AnalyzeRequest) -> AnalyzeResponse:
    if not predictor().ready:
        raise HTTPException(status_code=503, detail="Model not loaded. Train a baseline and set MODEL_PATH.")
    label, score = predictor().predict(body.text)
    return AnalyzeResponse(label=label, score=score, model_version="baseline-v0")
