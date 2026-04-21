"""
pytest -s -vv impl/backend/src/fastapi_app/router/signup/test_signup_verify_identity.py
"""
import os
from unittest.mock import patch, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.fastapi_app.router.signup.signup import router

# ─────────────────────────────────────────────
# テスト用アプリ
# ─────────────────────────────────────────────

app = FastAPI()
app.include_router(router)
client = TestClient(app, raise_server_exceptions=False)

SMTP_MOCK_TARGET = "src.modules.usecase.signup_verify_identity.repository.smtplib.SMTP"
USECASE_MOCK_TARGET = "src.fastapi_app.router.signup.signup.signup_verify_identity_usecase"

SEND_TO_EMAIL = os.getenv("TEST_SENDER_EMAIL")

# ─────────────────────────────────────────────
# 正常系
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/fastapi_app/router/signup/test_signup_verify_identity.py::TestSuccess
"""
class TestSuccess:

    def test_正常系_ステータス200が返る(self):
        with patch(SMTP_MOCK_TARGET) as mock_smtp:
            mock_smtp.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
            resp = client.post("/signup_verify_identity", json={"email": SEND_TO_EMAIL, "password": "1234"})
        assert resp.status_code == 200

    def test_正常系_okがTrueである(self):
        with patch(SMTP_MOCK_TARGET) as mock_smtp:
            mock_smtp.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
            resp = client.post("/signup_verify_identity", json={"email": SEND_TO_EMAIL, "password": "1234"})
        assert resp.json()["meta"]["ok"] is True

    def test_正常系_dataにcreate_utmsが含まれる(self):
        with patch(SMTP_MOCK_TARGET) as mock_smtp:
            mock_smtp.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
            resp = client.post("/signup_verify_identity", json={"email": SEND_TO_EMAIL, "password": "1234"})
        assert "create_utms" in resp.json()["data"]

    def test_正常系_create_utmsが整数である(self):
        with patch(SMTP_MOCK_TARGET) as mock_smtp:
            mock_smtp.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
            resp = client.post("/signup_verify_identity", json={"email": SEND_TO_EMAIL, "password": "1234"})
        assert isinstance(resp.json()["data"]["create_utms"], int)

    def test_正常系_errorsが空リストである(self):
        with patch(SMTP_MOCK_TARGET) as mock_smtp:
            mock_smtp.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
            resp = client.post("/signup_verify_identity", json={"email": SEND_TO_EMAIL, "password": "1234"})
        assert resp.json()["errors"] == []


# ─────────────────────────────────────────────
# 異常系: リクエスト不正 (400 ValueError)
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/fastapi_app/router/signup/test_signup_verify_identity.py::TestRequestError
"""
class TestRequestError:

    def test_異常系_emailなし_400が返る(self):
        resp = client.post("/signup_verify_identity", json={"password": "1234"})
        assert resp.status_code == 400

    def test_異常系_emailなし_okがFalseである(self):
        resp = client.post("/signup_verify_identity", json={"password": "1234"})
        assert resp.json()["meta"]["ok"] is False

    def test_異常系_emailなし_errorsにValueErrorが含まれる(self):
        resp = client.post("/signup_verify_identity", json={"password": "1234"})
        assert any("ValueError" in e for e in resp.json()["errors"])

    def test_異常系_passwordなし_400が返る(self):
        resp = client.post("/signup_verify_identity", json={"email": SEND_TO_EMAIL})
        assert resp.status_code == 400

    def test_異常系_passwordなし_errorsにValueErrorが含まれる(self):
        resp = client.post("/signup_verify_identity", json={"email": SEND_TO_EMAIL})
        assert any("ValueError" in e for e in resp.json()["errors"])

    def test_異常系_bodyなし_400が返る(self):
        resp = client.post("/signup_verify_identity", json={})
        assert resp.status_code == 400


# ─────────────────────────────────────────────
# 異常系: 不正email (400 InvalidEmailError)
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/fastapi_app/router/signup/test_signup_verify_identity.py::TestInvalidEmail
"""
class TestInvalidEmail:

    def test_異常系_不正email_atなし_400が返る(self):
        resp = client.post("/signup_verify_identity", json={"email": "invalidemail", "password": "1234"})
        assert resp.status_code == 400

    def test_異常系_不正email_atなし_errorsにInvalidEmailErrorが含まれる(self):
        resp = client.post("/signup_verify_identity", json={"email": "invalidemail", "password": "1234"})
        assert any("InvalidEmailError" in e for e in resp.json()["errors"])

    def test_異常系_不正email_ドメインなし_400が返る(self):
        resp = client.post("/signup_verify_identity", json={"email": "user@", "password": "1234"})
        assert resp.status_code == 400

    def test_異常系_不正email_空文字_400が返る(self):
        resp = client.post("/signup_verify_identity", json={"email": "", "password": "1234"})
        assert resp.status_code == 400

    def test_異常系_不正email_空白のみ_400が返る(self):
        resp = client.post("/signup_verify_identity", json={"email": "   ", "password": "1234"})
        assert resp.status_code == 400


# ─────────────────────────────────────────────
# 異常系: 不正password (400 InvalidPasswordError)
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/fastapi_app/router/signup/test_signup_verify_identity.py::TestInvalidPassword
"""
class TestInvalidPassword:

    def test_異常系_不正password_3桁_400が返る(self):
        resp = client.post("/signup_verify_identity", json={"email": SEND_TO_EMAIL, "password": "123"})
        assert resp.status_code == 400

    def test_異常系_不正password_3桁_errorsにInvalidPasswordErrorが含まれる(self):
        resp = client.post("/signup_verify_identity", json={"email": SEND_TO_EMAIL, "password": "123"})
        assert any("InvalidPasswordError" in e for e in resp.json()["errors"])

    def test_異常系_不正password_5桁_400が返る(self):
        resp = client.post("/signup_verify_identity", json={"email": SEND_TO_EMAIL, "password": "12345"})
        assert resp.status_code == 400

    def test_異常系_不正password_文字含む_400が返る(self):
        resp = client.post("/signup_verify_identity", json={"email": SEND_TO_EMAIL, "password": "12a4"})
        assert resp.status_code == 400

    def test_異常系_不正password_全角数字_400が返る(self):
        resp = client.post("/signup_verify_identity", json={"email": SEND_TO_EMAIL, "password": "１２３４"})
        assert resp.status_code == 400

    def test_異常系_不正password_空文字_400が返る(self):
        resp = client.post("/signup_verify_identity", json={"email": SEND_TO_EMAIL, "password": ""})
        assert resp.status_code == 400


# ─────────────────────────────────────────────
# 異常系: 内部エラー (500)
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/fastapi_app/router/signup/test_signup_verify_identity.py::TestInternalError
"""
class TestInternalError:

    def test_異常系_内部エラー_500が返る(self):
        with patch(USECASE_MOCK_TARGET, side_effect=RuntimeError("unexpected error")):
            resp = client.post("/signup_verify_identity", json={"email": SEND_TO_EMAIL, "password": "1234"})
        assert resp.status_code == 500

    def test_異常系_内部エラー_okがFalseである(self):
        with patch(USECASE_MOCK_TARGET, side_effect=RuntimeError("unexpected error")):
            resp = client.post("/signup_verify_identity", json={"email": SEND_TO_EMAIL, "password": "1234"})
        assert resp.json()["meta"]["ok"] is False

    def test_異常系_内部エラー_errorsにRuntimeErrorが含まれる(self):
        with patch(USECASE_MOCK_TARGET, side_effect=RuntimeError("unexpected error")):
            resp = client.post("/signup_verify_identity", json={"email": SEND_TO_EMAIL, "password": "1234"})
        assert any("RuntimeError" in e for e in resp.json()["errors"])
