import re
import traceback

from src.modules.application.application import ApplicationContext
from src.modules.helper.helper import unixtime_ms, uuid_hex, hash_string
from src.modules.usecase.signup_verify_identity.model import (
    InvalidEmailError,
    InvalidPasswordError,
    VerifyTokenData,
)
from src.modules.usecase.signup_verify_identity import repository

_EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


def validate_email(ctx: ApplicationContext, email: str) -> None:
    ctx.info(f"メールアドレス検証開始: email={email}")
    if not _EMAIL_PATTERN.match(email):
        ctx.error(f"メールアドレスが不正です: email={email}\n{traceback.format_exc()}")
        raise InvalidEmailError(f"Invalid email address: {email}")
    ctx.info("メールアドレス検証完了")


_PASSWORD_PATTERN = re.compile(r"^[0-9]{4}$")


def validate_password(ctx: ApplicationContext, password: str) -> None:
    ctx.info("パスワード検証開始")
    if not _PASSWORD_PATTERN.match(password):
        ctx.error(f"パスワードが不正です（4桁の数字である必要があります）\n{traceback.format_exc()}")
        raise InvalidPasswordError("Password must be a 4-digit number")
    ctx.info("パスワード検証完了")


def create_verify_token_data(
    ctx: ApplicationContext, email: str, password: str
) -> VerifyTokenData:
    ctx.info("ddbVerifyToken 用データ作成開始")
    cfg = ctx.config

    now_ms = unixtime_ms()
    verify_token = f"vtoken.{now_ms}.{uuid_hex()}"
    password_hash = hash_string(password.encode("utf-8"))
    ttl_expire_at = int(now_ms / 1000) + int(cfg.VTOKEN_LIFETIME_UTMS / 1000)

    data = VerifyTokenData(
        verify_token=verify_token,
        email=email,
        password_hash=password_hash,
        attempts=0,
        create_utms=now_ms,
        ttl_expire_at=ttl_expire_at,
    )
    ctx.info(f"ddbVerifyToken 用データ作成完了: verify_token={verify_token}")
    return data


def save_verify_token(ctx: ApplicationContext, data: VerifyTokenData) -> None:
    ctx.info(f"ddbVerifyToken 保存開始: verify_token={data.verify_token}")
    repository.save_verify_token(ctx, data)
    ctx.info("ddbVerifyToken 保存完了")


def send_verify_email(ctx: ApplicationContext, email: str, verify_token: str) -> None:
    ctx.info(f"検証メール送信開始: email={email}")
    repository.send_verify_email(ctx, email, verify_token)
    ctx.info("検証メール送信完了")
