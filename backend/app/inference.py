"""Artifact adapter: legacy baseline or audited ML-01 with explicit metadata."""
import os
from pathlib import Path
import joblib
from .preprocessing import clean_text
from ml.src.train_classic_models import sha256
from ml.src.explain import Explainer, DISCLAIMER

class Predictor:
    def __init__(self):
        self.pipeline = None
        self.explainer = None
        self.version = "baseline-v0"
        self.error = None
        path = os.getenv("MODEL_PATH")
        if not path:
            return
        try:
            report = os.getenv("MODEL_REPORT_PATH")
            if report:
                self.explainer = Explainer.from_artifacts(path, report, os.getenv("MODEL_CALIBRATION_PATH"))
                if self.explainer.calibrated and self.explainer.calibration is None:
                    raise ValueError("ML-01 SVM requires MODEL_CALIBRATION_PATH")
                if not hasattr(self.explainer.pipeline.steps[-1][1], "intercept_"):
                    raise ValueError("This adapter requires a linear classifier with intercept")
                if self.explainer.calibrated and self.explainer.calibration.get("model_sha256") != sha256(Path(path)):
                    raise ValueError("Calibration does not match model checksum; rerun calibrate_selected")
                self.pipeline = self.explainer.pipeline
                self.version = self.explainer.model_version
            else:
                self.pipeline = joblib.load(Path(path))
                if not hasattr(self.pipeline, "predict_proba"):
                    raise ValueError("Audited SVM requires MODEL_REPORT_PATH and MODEL_CALIBRATION_PATH")
        except (OSError, ValueError, TypeError, KeyError) as exc:
            self.pipeline = None
            self.explainer = None
            self.error = str(exc)

    @property
    def ready(self):
        return self.pipeline is not None

    def analyze(self, text):
        if not self.ready:
            raise RuntimeError("No model artifact loaded")
        if self.explainer:
            e = self.explainer
            cleaned = e.cleaner(text)
            if not cleaned.strip():
                raise ValueError("Text is empty after source-marker cleaning")
            score = float(e.predict_proba([cleaned])[0][e.fake_index])
            label = "SUSPICIOUS" if e.pipeline.predict([cleaned])[0] == e.fake_label else "LESS_SUSPICIOUS"
            explanation = e.contributions(cleaned)
            explanation["disclaimer"] = DISCLAIMER
            # LIME is optional because it evaluates 1000 perturbations per article.
            if os.getenv("ENABLE_LIME", "false").lower() == "true":
                try:
                    explanation["lime"] = e.explain(cleaned, already_clean=True)
                except ImportError:
                    explanation["lime_unavailable"] = True
            return dict(label=label, score=score, model_version=self.version,
                        score_kind="calibrated_fake_score" if e.calibrated else "model_probability",
                        explanation=explanation)
        cleaned = clean_text(text)
        if not cleaned.strip():
            raise ValueError("Text is empty after cleaning")
        score = float(self.pipeline.predict_proba([cleaned])[0][list(self.pipeline.classes_).index(1)])
        return dict(label="SUSPICIOUS" if score >= .5 else "LESS_SUSPICIOUS", score=score,
                    model_version=self.version, score_kind="model_probability", explanation=None)

    def predict(self, text):
        result = self.analyze(text)
        return result["label"], result["score"]
