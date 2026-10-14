"""Load the trained artifact once per API process."""

import os
from pathlib import Path

import joblib

from .preprocessing import clean_text


class Predictor:
    def __init__(self) -> None:
        self.pipeline = None
        model_path = os.getenv("MODEL_PATH")
        if model_path:
            path = Path(model_path)
            if not path.is_file():
                raise RuntimeError(f"MODEL_PATH does not exist: {path}")
            self.pipeline = joblib.load(path)

    @property
    def ready(self) -> bool:
        return self.pipeline is not None

    def predict(self, text: str) -> tuple[str, float]:
        if self.pipeline is None:
            raise RuntimeError("No model artifact loaded")
        probabilities = self.pipeline.predict_proba([clean_text(text)])[0]
        fake_index = list(self.pipeline.classes_).index(1)
        score = float(probabilities[fake_index])
        return ("SUSPICIOUS" if score >= 0.5 else "LESS_SUSPICIOUS", score)
