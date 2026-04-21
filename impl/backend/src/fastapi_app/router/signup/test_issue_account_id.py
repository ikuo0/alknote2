"""
pytest -s -vv impl/backend/src/fastapi_app/router/signup/test_issue_account_id.py
"""
import inspect
import os
import time
from unittest.mock import patch, MagicMock

import boto3
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.fastapi_app.router.signup.signup import router
from src.modules.config.config import get_config, Config
from src.modules.helper.helper import unixtime_ms, uuid_hex, hash_string

# ─────────────────────────────────────────────
# テスト用アプリ
# ─────────────────────────────────────────────

app = FastAPI()
app.include_router(router)
client = TestClient(app, raise_server_exceptions=False)

SMTP_MOCK_TARGET = "src.modules.usecase.issue_account_id.repository.smtplib.SMTP"
USECASE_MOCK_TARGET = "src.fastapi_app.router.signup.signup.issue_account_id_usecase"

EMAIL_RECIPIENT = os.environ["TEST_SENDER_EMAIL"]

# ─────────────────────────────────────────────
# DDB ヘルパー
# ─────────────────────────────────────────────

def _cfg() -> Config:
    return get_config("local")


def _ddb():
    cfg = _cfg()
    return boto3.client(
        "dynamodb",
        region_name=cfg.DDB_REGION,
        endpoint_url=f"http://{cfg.DDB_HOST}",
        aws_access_key_id=cfg.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=cfg.AWS_SECRET_ACCESS_KEY,
    )


def make_verify_token() -> str:
    return f"vtoken.{unixtime_ms()}.{uuid_hex()}"


def insert_verify_token(
    verify_token: str,
    email: str,
    password_hash: str,
    attempts: int,
    ttl_expire_at: int,
) -> None:
    _ddb().put_item(
        TableName="ddbVerifyToken",
        Item={
            "verify_token": {"S": verify_token},
            "email": {"S": email},
            "password_hash": {"S": password_hash},
            "attempts": {"N": str(attempts)},
            "create_utms": {"N": str(unixtime_ms())},
            "ttl_expire_at": {"N": str(ttl_expire_at)},
        },
    )


def fetch_verify_token_item(verify_token: str) -> dict | None:
    resp = _ddb().get_item(
        TableName="ddbVerifyToken",
        Key={"verify_token": {"S": verify_token}},
    )
    return resp.get("Item")


def future_ttl() -> int:
    return int(time.time()) + 3600


def past_ttl() -> int:
    return 1


def dumpvars(**kwargs):
    print("\n" + "#" * 100)
    for name, value in kwargs.items():
        print(f"{name} = {value!r}")

# ─────────────────────────────────────────────
# 正常系
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/fastapi_app/router/signup/test_issue_account_id.py::TestSuccess
"""
class TestSuccess:

    def _post(self, verify_token: str, password: str):
        with patch(SMTP_MOCK_TARGET) as mock_smtp:
            mock_smtp.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
            return client.post("/issue_account_id", json={"verify_token": verify_token, "password": password})

    def test_正常系_ステータス200が返る(self):
        password = "1234"
        vtoken = make_verify_token()
        insert_verify_token(vtoken, EMAIL_RECIPIENT, hash_string(password.encode()), 0, future_ttl())
        resp = self._post(vtoken, password)
        assert resp.status_code == 200
        dumpvars(function=inspect.currentframe().f_code.co_name, verify_token=vtoken, password=password, status_code=resp.status_code)
        print(resp.json())

    def test_正常系_okがTrueである(self):
        password = "1234"
        vtoken = make_verify_token()
        insert_verify_token(vtoken, EMAIL_RECIPIENT, hash_string(password.encode()), 0, future_ttl())
        resp = self._post(vtoken, password)
        assert resp.json()["meta"]["ok"] is True

    def test_正常系_dataにaccount_idが含まれる(self):
        password = "1234"
        vtoken = make_verify_token()
        insert_verify_token(vtoken, EMAIL_RECIPIENT, hash_string(password.encode()), 0, future_ttl())
        resp = self._post(vtoken, password)
        assert "account_id" in resp.json()["data"]

    def test_正常系_account_idがaidプレフィックスである(self):
        password = "1234"
        vtoken = make_verify_token()
        insert_verify_token(vtoken, EMAIL_RECIPIENT, hash_string(password.encode()), 0, future_ttl())
        resp = self._post(vtoken, password)
        assert resp.json()["data"]["account_id"].startswith("aid.")

    def test_正常系_dataにexpiry_utmsが含まれる(self):
        password = "1234"
        vtoken = make_verify_token()
        insert_verify_token(vtoken, EMAIL_RECIPIENT, hash_string(password.encode()), 0, future_ttl())
        resp = self._post(vtoken, password)
        assert "expiry_utms" in resp.json()["data"]

    def test_正常系_expiry_utmsが現在時刻より未来である(self):
        password = "1234"
        vtoken = make_verify_token()
        insert_verify_token(vtoken, EMAIL_RECIPIENT, hash_string(password.encode()), 0, future_ttl())
        before_ms = unixtime_ms()
        resp = self._post(vtoken, password)
        assert resp.json()["data"]["expiry_utms"] > before_ms

    def test_正常系_errorsが空リストである(self):
        password = "1234"
        vtoken = make_verify_token()
        insert_verify_token(vtoken, EMAIL_RECIPIENT, hash_string(password.encode()), 0, future_ttl())
        resp = self._post(vtoken, password)
        assert resp.json()["errors"] == []


# ─────────────────────────────────────────────
# 異常系: リクエスト不正 (400 ValueError)
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/fastapi_app/router/signup/test_issue_account_id.py::TestRequestError
"""
class TestRequestError:

    def test_異常系_verify_tokenなし_400が返る(self):
        resp = client.post("/issue_account_id", json={"password": "1234"})
        assert resp.status_code == 400

    def test_異常系_verify_tokenなし_okがFalseである(self):
        resp = client.post("/issue_account_id", json={"password": "1234"})
        assert resp.json()["meta"]["ok"] is False

    def test_異常系_verify_tokenなし_errorsにValueErrorが含まれる(self):
        resp = client.post("/issue_account_id", json={"password": "1234"})
        assert any("ValueError" in e for e in resp.json()["errors"])

    def test_異常系_passwordなし_400が返る(self):
        resp = client.post("/issue_account_id", json={"verify_token": "vtoken.0.dummy"})
        assert resp.status_code == 400

    def test_異常系_bodyなし_400が返る(self):
        resp = client.post("/issue_account_id", json={})
        assert resp.status_code == 400


# ─────────────────────────────────────────────
# 異常系: 存在しないトークン (400 InvalidTokenError)
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/fastapi_app/router/signup/test_issue_account_id.py::TestInvalidToken
"""
class TestInvalidToken:

    def test_異常系_存在しないトークン_400が返る(self):
        non_existent = f"vtoken.0.nonexistent_{uuid_hex()}"
        resp = client.post("/issue_account_id", json={"verify_token": non_existent, "password": "1234"})
        assert resp.status_code == 400

    def test_異常系_存在しないトークン_okがFalseである(self):
        non_existent = f"vtoken.0.nonexistent_{uuid_hex()}"
        resp = client.post("/issue_account_id", json={"verify_token": non_existent, "password": "1234"})
        assert resp.json()["meta"]["ok"] is False

    def test_異常系_存在しないトークン_errorsにInvalidTokenErrorが含まれる(self):
        non_existent = f"vtoken.0.nonexistent_{uuid_hex()}"
        resp = client.post("/issue_account_id", json={"verify_token": non_existent, "password": "1234"})
        assert any("InvalidTokenError" in e for e in resp.json()["errors"])


# ─────────────────────────────────────────────
# 異常系: attempts 超過 (400 TooManyAttemptsError)
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/fastapi_app/router/signup/test_issue_account_id.py::TestTooManyAttempts
"""
class TestTooManyAttempts:

    def test_異常系_attempts超過_400が返る(self):
        password = "1234"
        vtoken = make_verify_token()
        insert_verify_token(vtoken, EMAIL_RECIPIENT, hash_string(password.encode()), 3, future_ttl())
        resp = client.post("/issue_account_id", json={"verify_token": vtoken, "password": password})
        assert resp.status_code == 400

    def test_異常系_attempts超過_errorsにTooManyAttemptsErrorが含まれる(self):
        password = "1234"
        vtoken = make_verify_token()
        insert_verify_token(vtoken, EMAIL_RECIPIENT, hash_string(password.encode()), 3, future_ttl())
        resp = client.post("/issue_account_id", json={"verify_token": vtoken, "password": password})
        assert any("TooManyAttemptsError" in e for e in resp.json()["errors"])


# ─────────────────────────────────────────────
# 異常系: トークン期限切れ (400 TokenExpiredError)
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/fastapi_app/router/signup/test_issue_account_id.py::TestTokenExpired
"""
class TestTokenExpired:

    def test_異常系_期限切れトークン_400が返る(self):
        password = "1234"
        vtoken = make_verify_token()
        insert_verify_token(vtoken, EMAIL_RECIPIENT, hash_string(password.encode()), 0, past_ttl())
        resp = client.post("/issue_account_id", json={"verify_token": vtoken, "password": password})
        assert resp.status_code == 400

    def test_異常系_期限切れトークン_errorsにTokenExpiredErrorが含まれる(self):
        password = "1234"
        vtoken = make_verify_token()
        insert_verify_token(vtoken, EMAIL_RECIPIENT, hash_string(password.encode()), 0, past_ttl())
        resp = client.post("/issue_account_id", json={"verify_token": vtoken, "password": password})
        assert any("TokenExpiredError" in e for e in resp.json()["errors"])


# ─────────────────────────────────────────────
# 異常系: パスワード不一致 (400 InvalidPasswordError)
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/fastapi_app/router/signup/test_issue_account_id.py::TestInvalidPassword
"""
class TestInvalidPassword:

    def test_異常系_パスワード不一致_400が返る(self):
        correct = "1234"
        wrong = "9999"
        vtoken = make_verify_token()
        insert_verify_token(vtoken, EMAIL_RECIPIENT, hash_string(correct.encode()), 0, future_ttl())
        resp = client.post("/issue_account_id", json={"verify_token": vtoken, "password": wrong})
        assert resp.status_code == 400

    def test_異常系_パスワード不一致_errorsにInvalidPasswordErrorが含まれる(self):
        correct = "1234"
        wrong = "9999"
        vtoken = make_verify_token()
        insert_verify_token(vtoken, EMAIL_RECIPIENT, hash_string(correct.encode()), 0, future_ttl())
        resp = client.post("/issue_account_id", json={"verify_token": vtoken, "password": wrong})
        assert any("InvalidPasswordError" in e for e in resp.json()["errors"])

    def test_異常系_パスワード不一致後attemptsがインクリメントされる(self):
        correct = "1234"
        wrong = "9999"
        vtoken = make_verify_token()
        insert_verify_token(vtoken, EMAIL_RECIPIENT, hash_string(correct.encode()), 0, future_ttl())
        client.post("/issue_account_id", json={"verify_token": vtoken, "password": wrong})
        item = fetch_verify_token_item(vtoken)
        assert item is not None
        assert int(item["attempts"]["N"]) == 1


# ─────────────────────────────────────────────
# 異常系: 内部エラー (500)
# ─────────────────────────────────────────────

"""
pytest -s -vv impl/backend/src/fastapi_app/router/signup/test_issue_account_id.py::TestInternalError
"""
class TestInternalError:

    def test_異常系_内部エラー_500が返る(self):
        with patch(USECASE_MOCK_TARGET, side_effect=RuntimeError("unexpected error")):
            resp = client.post("/issue_account_id", json={"verify_token": "vtoken.0.dummy", "password": "1234"})
        assert resp.status_code == 500

    def test_異常系_内部エラー_okがFalseである(self):
        with patch(USECASE_MOCK_TARGET, side_effect=RuntimeError("unexpected error")):
            resp = client.post("/issue_account_id", json={"verify_token": "vtoken.0.dummy", "password": "1234"})
        assert resp.json()["meta"]["ok"] is False

    def test_異常系_内部エラー_errorsにRuntimeErrorが含まれる(self):
        with patch(USECASE_MOCK_TARGET, side_effect=RuntimeError("unexpected error")):
            resp = client.post("/issue_account_id", json={"verify_token": "vtoken.0.dummy", "password": "1234"})
        assert any("RuntimeError" in e for e in resp.json()["errors"])
