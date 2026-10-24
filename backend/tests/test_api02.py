import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

_had_secret = "SECRET_KEY" in os.environ
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-api02-unit-tests-123456789")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app import models
from backend.app.auth import get_password_hash
from backend.app.database import Base, get_db
from backend.app.main import app

if not _had_secret:
    os.environ.pop("SECRET_KEY", None)


engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Session = sessionmaker(bind=engine)


def test_db():
    with Session() as db:
        yield db


class Api02Tests(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        app.dependency_overrides[get_db] = test_db
        self.client = TestClient(app)
        self.predictor = patch("backend.app.main.predictor")
        self.model = self.predictor.start().return_value
        self.model.ready = True
        self.model.predict.return_value = ("SUSPICIOUS", 0.85)

    def tearDown(self):
        self.predictor.stop()
        self.client.close()
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)

    def login(self, email):
        response = self.client.post("/api/v1/auth/register", json={"email": email, "password": "Password123"})
        self.assertEqual(response.status_code, 201, response.text)
        response = self.client.post("/api/v1/auth/login", json={"email": email, "password": "Password123"})
        self.assertEqual(response.status_code, 200, response.text)
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    def analyze(self, headers=None):
        response = self.client.post("/api/v1/analyze", json={"text": "A sample news article. " * 8}, headers=headers or {})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_user_history_feedback_and_admin_are_isolated(self):
        alice = self.login("alice@example.com")
        bob = self.login("bob@example.com")
        alice_id = self.analyze(alice)["id"]
        bob_id = self.analyze(bob)["id"]
        self.assertNotEqual(alice_id, bob_id)

        alice_history = self.client.get("/api/v1/analyses?limit=1&offset=0", headers=alice)
        self.assertEqual(alice_history.status_code, 200)
        self.assertEqual(alice_history.json()["total"], 1)
        self.assertEqual([row["id"] for row in alice_history.json()["items"]], [alice_id])
        self.assertEqual(self.client.get("/api/v1/analyses", headers=bob).json()["items"][0]["id"], bob_id)
        self.assertEqual(self.client.get("/api/v1/analyses").status_code, 401)
        self.assertEqual(self.client.get("/api/v1/analyses?limit=51", headers=alice).status_code, 422)

        other_feedback = self.client.post(f"/api/v1/analyses/{alice_id}/feedback", headers=bob, json={"agree": False})
        self.assertEqual(other_feedback.status_code, 404)
        feedback = self.client.post(f"/api/v1/analyses/{alice_id}/feedback", headers=alice,
                                    json={"agree": False, "comment": "Disputed result"})
        self.assertEqual(feedback.status_code, 201, feedback.text)
        self.assertEqual(self.client.post(f"/api/v1/analyses/{alice_id}/feedback", headers=alice,
                                          json={"agree": True}).status_code, 409)
        self.assertEqual(self.client.get("/api/v1/analyses", headers=alice).json()["items"][0]["feedback"]["agree"], False)
        self.assertEqual(self.client.get("/api/v1/admin/summary", headers=alice).status_code, 403)
        self.assertEqual(self.client.get("/api/v1/admin/disputed", headers=bob).status_code, 403)

        with Session() as db:
            db.add(models.User(email="admin@example.com", hashed_password=get_password_hash("Password123"), role=models.Role.ADMIN))
            db.commit()
        response = self.client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "Password123"})
        admin = {"Authorization": f"Bearer {response.json()['access_token']}"}
        self.assertEqual(self.client.get("/api/v1/admin/summary", headers=admin).json(), {
            "total_users": 3, "total_analyses": 2, "total_feedbacks": 1, "disputed_feedbacks": 1,
        })
        disputed = self.client.get("/api/v1/admin/disputed?limit=1&offset=0", headers=admin)
        self.assertEqual(disputed.status_code, 200)
        self.assertEqual(disputed.json()["total"], 1)
        self.assertEqual(disputed.json()["items"][0]["analysis_id"], alice_id)

    def test_anonymous_result_is_not_saved_and_bad_token_is_rejected(self):
        self.assertIsNone(self.analyze()["id"])
        self.assertEqual(self.client.post("/api/v1/analyze", json={"text": "A sample news article. " * 8},
                                          headers={"Authorization": "Bearer invalid"}).status_code, 401)
        self.assertEqual(self.client.post("/api/v1/analyze", json={"text": "A sample news article. " * 8},
                                          headers={"Authorization": "Basic invalid"}).status_code, 401)
        self.assertEqual(self.client.get("/api/v1/admin/summary").status_code, 401)
        with Session() as db:
            self.assertEqual(db.query(models.Analysis).count(), 0)

    def test_pagination_and_agreement_do_not_create_dispute(self):
        alice = self.login("alice@example.com")
        ids = [self.analyze(alice)["id"] for _ in range(3)]
        page = self.client.get("/api/v1/analyses?limit=1&offset=1", headers=alice).json()
        self.assertEqual(page["total"], 3)
        self.assertEqual([item["id"] for item in page["items"]], [ids[1]])
        self.assertEqual(self.client.post(f"/api/v1/analyses/{ids[0]}/feedback", headers=alice,
                                          json={"agree": True}).status_code, 201)
        with Session() as db:
            self.assertEqual(db.query(models.Feedback).count(), 1)
            self.assertEqual(db.query(models.Feedback).filter(models.Feedback.agree.is_(False)).count(), 0)

    def test_migration_upgrades_existing_users_database(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as directory:
            url = f"sqlite:///{Path(directory) / 'existing.db'}"
            env = {**os.environ, "DATABASE_URL": url}
            def upgrade(revision):
                subprocess.run([sys.executable, "-m", "alembic", "upgrade", revision], cwd=root,
                               env=env, capture_output=True, text=True, check=True)

            upgrade("0f4b5cae6a63")
            existing_engine = create_engine(url)
            with existing_engine.begin() as connection:
                connection.execute(text("INSERT INTO users (email, hashed_password, role, created_at) "
                                        "VALUES ('existing@example.com', 'hash', 'USER', CURRENT_TIMESTAMP)"))
            upgrade("head")
            with existing_engine.connect() as connection:
                self.assertEqual(connection.execute(text("SELECT COUNT(*) FROM users")).scalar_one(), 1)
                self.assertEqual({"analyses", "feedbacks"}.issubset(inspect(connection).get_table_names()), True)
                self.assertEqual(connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one(), "6b74a2d90f31")
            existing_engine.dispose()


if __name__ == "__main__":
    unittest.main()
