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
        response = self.client.post(
            "/api/v1/analyze",
            json={"text": "A sufficiently long article for testing the endpoint response without a trained model artifact. " * 2},
        )
        self.assertEqual(response.status_code, 503)

    def test_short_input_is_rejected(self):
        self.assertEqual(self.client.post("/api/v1/analyze", json={"text": "short"}).status_code, 422)

    def test_auth_flow_register_login_and_me(self):
        register_payload = {
            "email": "tester@example.com",
            "password": "Password123",
            "role": "USER",
        }
        res_register = self.client.post("/api/v1/auth/register", json=register_payload)
        self.assertEqual(res_register.status_code, 201)
        self.assertEqual(res_register.json()["email"], "tester@example.com")

        login_payload = {
            "email": "tester@example.com",
            "password": "Password123",
        }
        res_login = self.client.post("/api/v1/auth/login", json=login_payload)
        self.assertEqual(res_login.status_code, 200)
        token = res_login.json().get("access_token")
        self.assertIsNotNone(token)

        headers = {"Authorization": f"Bearer {token}"}
        res_me = self.client.get("/api/v1/auth/me", headers=headers)
        self.assertEqual(res_me.status_code, 200)
        self.assertEqual(res_me.json()["email"], "tester@example.com")
        self.assertEqual(res_me.json()["role"], "USER")

    def test_login_invalid_credentials(self):
        bad_payload = {
            "email": "admin@example.com",
            "password": "WrongPassword",
        }
        res = self.client.post("/api/v1/auth/login", json=bad_payload)
        self.assertEqual(res.status_code, 401)


if __name__ == "__main__":
    unittest.main()
