import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from backend.app.inference import Predictor
from ml.src.explain import Explainer, fit_platt
from ml.src.train_classic_models import sha256

class Ml01InferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.texts = ["read more shocking hoax", "read more secret outrage", "minister said budget approved", "officials said policy approved"] * 5
        self.labels = [0, 0, 1, 1] * 5
        self.model = Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1,2))), ("classifier", LinearSVC(random_state=42))]).fit(self.texts, self.labels)
        joblib.dump(self.model, self.root / "model.joblib")
        (self.root / "report.json").write_text(json.dumps({"label_map":{"0":"Fake","1":"Real"}, "experiment":"test", "selected_model":"svm"}))
        cal = fit_platt(self.model.decision_function(self.texts), np.array(self.labels) == 0)
        cal["model_sha256"] = sha256(self.root / "model.joblib")
        (self.root / "cal.json").write_text(json.dumps(cal))
        self.env = patch.dict(os.environ, {"MODEL_PATH": str(self.root / "model.joblib"), "MODEL_REPORT_PATH": str(self.root / "report.json"), "MODEL_CALIBRATION_PATH": str(self.root / "cal.json"), "ENABLE_LIME":"false"})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_fake_mapping_and_exact_bigram_decomposition(self):
        predictor = Predictor()
        self.assertTrue(predictor.ready, predictor.error)
        result = predictor.analyze("read more shocking hoax")
        self.assertEqual(result["label"], "SUSPICIOUS")
        self.assertGreater(result["score"], .5)
        exp = result["explanation"]
        self.assertIn("read more", [t["term"] for t in exp["terms"]])
        total = exp["intercept"] + exp["other_contribution"] + sum(t["value"] for t in exp["terms"])
        self.assertAlmostEqual(total, -self.model.decision_function(["read more shocking hoax"])[0])
        self.assertAlmostEqual(total, exp["fake_margin"])
        self.assertEqual(result["model_version"], "test:svm")
        self.assertEqual(predictor.analyze("minister said budget approved")["label"], "LESS_SUSPICIOUS")

    def test_missing_or_mismatched_calibration_is_unavailable(self):
        with patch.dict(os.environ, {"MODEL_CALIBRATION_PATH":""}):
            self.assertFalse(Predictor().ready)
        (self.root / "cal.json").write_text('{"model_sha256":"wrong"}')
        self.assertFalse(Predictor().ready)

    def test_empty_cleaned_input_is_rejected(self):
        with self.assertRaises(ValueError):
            Predictor().analyze("(Reuters) -")

    def test_margin_reconstruction_with_top_k_remainder(self):
        exp = Explainer(self.model, 0).contributions(self.texts[0], top_k=1)
        self.assertNotEqual(exp["other_contribution"], 0)
        self.assertAlmostEqual(exp["intercept"] + exp["other_contribution"] + exp["terms"][0]["value"], exp["fake_margin"])

    def test_api_returns_explanation_and_artifact_version(self):
        from fastapi.testclient import TestClient
        from backend.app.main import app, predictor, get_optional_user
        from backend.app.database import get_db
        def no_db():
            yield None
        previous = app.dependency_overrides.copy()
        app.dependency_overrides[get_db] = no_db
        app.dependency_overrides[get_optional_user] = lambda: None
        try:
            with patch('backend.app.main.predictor', return_value=Predictor()):
                with TestClient(app) as client:
                    result = client.post('/api/v1/analyze', json={'text': 'read more shocking hoax ' * 8})
                    self.assertEqual(result.status_code, 200, result.text)
                    self.assertEqual(result.json()['model_version'], 'test:svm')
                    self.assertIsNone(result.json()['id'])
                    self.assertEqual(result.json()['explanation']['method'], 'tfidf_times_coefficient')
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous)
