import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from datetime import timedelta
from unittest.mock import patch

_had_secret = "SECRET_KEY" in os.environ
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unittest-test-secret-key-for-unittest")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from typing import Annotated
from fastapi import Depends
from jose import jwt

from backend.app.main import app, predictor, require_admin
from backend.app.database import Base, get_db
from backend.app import models
from backend.app.auth import create_access_token, get_password_hash

if not _had_secret:
    os.environ.pop("SECRET_KEY", None)

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/v1/admin/test-only")
def admin_test_route(admin: Annotated[models.User, Depends(require_admin)]):
    return {"status": "ok", "admin_email": admin.email}

class ApiTests(unittest.TestCase):
    def setUp(self):
        app.dependency_overrides[get_db] = override_get_db
        self.environment = patch.dict(os.environ, {"MODEL_PATH": ""})
        self.environment.start()
        predictor.cache_clear()
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        predictor.cache_clear()
        self.environment.stop()

    def _register_and_login(self, email="tester@example.com", password="Password123"):
        self.client.post("/api/v1/auth/register", json={"email": email, "password": password})
        res = self.client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return {"Authorization": f"Bearer {res.json()['access_token']}"}

    def test_health_reports_missing_artifact(self):
        self.assertEqual(self.client.get("/health").json(), {"status": "ok", "model_loaded": False})

    def test_no_model_returns_service_unavailable(self):
        res = self.client.post("/api/v1/analyze", json={"text": "A long test text " * 20})
        self.assertEqual(res.status_code, 503)

    def test_short_input_is_rejected(self):
        self.assertEqual(self.client.post("/api/v1/analyze", json={"text": "short"}).status_code, 422)

    def test_register_mass_assignment_blocked(self):
        res = self.client.post(
            "/api/v1/auth/register",
            json={"email": "hacker@example.com", "password": "password123", "role": "ADMIN"}
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()["role"], "USER")

    def test_duplicate_email_rejected(self):
        payload = {"email": "dup@example.com", "password": "Password123"}
        self.assertEqual(self.client.post("/api/v1/auth/register", json=payload).status_code, 201)
        self.assertEqual(self.client.post("/api/v1/auth/register", json=payload).status_code, 400)

    def test_wrong_password_for_existing_user(self):
        self._register_and_login("a@example.com", "Password123")
        res = self.client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": "WrongPassword!"})
        self.assertEqual(res.status_code, 401)

    def test_me_without_token_rejected(self):
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 401)

    def test_forged_token_rejected(self):
        forged = jwt.encode({"sub": "tester@example.com"}, "fake-key-very-long-1234567890", algorithm="HS256")
        res = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged}"})
        self.assertEqual(res.status_code, 401)

    def test_expired_token_rejected(self):
        token = create_access_token({"sub": "e@example.com", "role": "USER"}, expires_delta=timedelta(seconds=-1))
        res = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.status_code, 401)

    def test_token_for_nonexistent_user_rejected(self):
        token = create_access_token({"sub": "ghost@example.com", "role": "USER"})
        res = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.status_code, 401)

    def test_password_over_72_bytes_rejected(self):
        res = self.client.post("/api/v1/auth/register", json={"email": "long@example.com", "password": "a" * 73})
        self.assertEqual(res.status_code, 422)

    def test_missing_secret_prevents_startup(self):
        environment = os.environ.copy()
        environment.pop("SECRET_KEY", None)
        result = subprocess.run(
            [sys.executable, "-c", "import backend.app.main"],
            cwd=Path(__file__).resolve().parents[2],
            env=environment,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SECRET_KEY", result.stderr)

    def test_migrations_on_empty_database_support_auth(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as directory:
            url = f"sqlite:///{Path(directory) / 'new.sqlite'}"
            environment = {**os.environ, "DATABASE_URL": url}
            subprocess.run(
                [sys.executable, "-m", "alembic", "upgrade", "head"],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                check=True,
            )
            migrated_engine = create_engine(url, connect_args={"check_same_thread": False})
            migrated_sessions = sessionmaker(bind=migrated_engine)

            def migrated_db():
                with migrated_sessions() as db:
                    yield db

            app.dependency_overrides[get_db] = migrated_db
            try:
                response = self.client.post(
                    "/api/v1/auth/register",
                    json={"email": "new@example.com", "password": "Password123"},
                )
                self.assertEqual(response.status_code, 201, response.text)
                response = self.client.post(
                    "/api/v1/auth/login",
                    json={"email": "new@example.com", "password": "Password123"},
                )
                self.assertEqual(response.status_code, 200, response.text)
                token = response.json()["access_token"]
                response = self.client.get(
                    "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
                )
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.json()["email"], "new@example.com")
            finally:
                app.dependency_overrides[get_db] = override_get_db
                migrated_engine.dispose()

    def test_user_cannot_access_admin_route(self):
        headers = self._register_and_login("user@example.com")
        self.assertEqual(self.client.get("/api/v1/admin/test-only", headers=headers).status_code, 403)

    def test_admin_can_access_admin_route(self):
        with TestingSessionLocal() as db:
            db.add(models.User(email="boss@example.com", hashed_password=get_password_hash("Boss123"), role=models.Role.ADMIN))
            db.commit()
        
        res = self.client.post("/api/v1/auth/login", json={"email": "boss@example.com", "password": "Boss123"})
        headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
        
        test_admin_res = self.client.get("/api/v1/admin/test-only", headers=headers)
        self.assertEqual(test_admin_res.status_code, 200)

if __name__ == "__main__":
    unittest.main()
