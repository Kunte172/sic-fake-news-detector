import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app, predictor


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {"MODEL_PATH": ""})
        self.environment.start()
        predictor.cache_clear()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        predictor.cache_clear()
        self.environment.stop()

    def test_health_reports_missing_artifact(self):
        self.assertEqual(self.client.get("/health").json(), {"status": "ok", "model_loaded": False})

    def test_no_model_returns_service_unavailable(self):
        response = self.client.post("/api/v1/analyze", json={"text": "A sufficiently long article for testing the endpoint response without a trained model artifact. " * 2})
        self.assertEqual(response.status_code, 503)

    def test_short_input_is_rejected(self):
        self.assertEqual(self.client.post("/api/v1/analyze", json={"text": "short"}).status_code, 422)


if __name__ == "__main__":
    unittest.main()
