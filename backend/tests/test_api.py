import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.app.main import app, predictor

# SQLite in-memory dùng riêng cho test suite
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {"MODEL_PATH": ""})
        self.environment.start()
        predictor.cache_clear()
        Base.metadata.create_all(bind=engine_test)
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        Base.metadata.drop_all(bind=engine_test)
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

    def test_history_and_feedback_flow(self):
        # 1. Đăng ký & đăng nhập
        self.client.post("/api/v1/auth/register", json={"email": "u1@example.com", "password": "Password123"})
        token_u1 = self.client.post("/api/v1/auth/login", json={"email": "u1@example.com", "password": "Password123"}).json()["access_token"]
        headers_u1 = {"Authorization": f"Bearer {token_u1}"}

        # 2. Kiểm tra danh sách rỗng ban đầu
        res_history = self.client.get("/api/v1/analyses", headers=headers_u1)
        self.assertEqual(res_history.status_code, 200)
        self.assertEqual(res_history.json()["total"], 0)

        # 3. Tạo một bản ghi phân tích trực tiếp qua DB test
        db = TestingSessionLocal()
        from backend.app.models import Analysis, User
        user = db.query(User).filter_by(email="u1@example.com").first()
        analysis = Analysis(
            user_id=user.id,
            input_type="text",
            content_preview="Preview text...",
            label="SUSPICIOUS",
            score=0.85,
            model_version="baseline-v0",
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        analysis_id = analysis.id
        db.close()

        # 4. Kiểm tra phân trang và lịch sử người dùng
        res_history_after = self.client.get("/api/v1/analyses?limit=10&offset=0", headers=headers_u1)
        self.assertEqual(res_history_after.status_code, 200)
        self.assertEqual(res_history_after.json()["total"], 1)

        # 5. Gửi feedback
        res_fb = self.client.post(
            f"/api/v1/analyses/{analysis_id}/feedback",
            json={"agree": False, "comment": "Mô hình nhận nhầm"},
            headers=headers_u1,
        )
        self.assertEqual(res_fb.status_code, 201)

        # 6. Admin kiểm tra thống kê và các ca phản đối
        self.client.post("/api/v1/auth/register", json={"email": "admin2@example.com", "password": "Password123", "role": "ADMIN"})
        token_admin = self.client.post("/api/v1/auth/login", json={"email": "admin2@example.com", "password": "Password123"}).json()["access_token"]
        headers_admin = {"Authorization": f"Bearer {token_admin}"}

        res_summary = self.client.get("/api/v1/admin/summary", headers=headers_admin)
        self.assertEqual(res_summary.status_code, 200)
        self.assertEqual(res_summary.json()["disputed_feedbacks"], 1)

        res_disputed = self.client.get("/api/v1/admin/disputed", headers=headers_admin)
        self.assertEqual(res_disputed.status_code, 200)
        self.assertEqual(res_disputed.json()["total"], 1)


if __name__ == "__main__":
    unittest.main()