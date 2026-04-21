import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import boto3

from src.modules.application.application import ApplicationContext
from src.modules.usecase.signup_verify_identity.model import VerifyTokenData


def save_verify_token(ctx: ApplicationContext, data: VerifyTokenData) -> None:
    cfg = ctx.config
    client = boto3.client(
        "dynamodb",
        region_name=cfg.DDB_REGION,
        endpoint_url=f"http://{cfg.DDB_HOST}",
        aws_access_key_id=cfg.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=cfg.AWS_SECRET_ACCESS_KEY,
    )
    client.put_item(
        TableName="ddbVerifyToken",
        Item={
            "verify_token": {"S": data.verify_token},
            "email": {"S": data.email},
            "password_hash": {"S": data.password_hash},
            "attempts": {"N": str(data.attempts)},
            "create_utms": {"N": str(data.create_utms)},
            "ttl_expire_at": {"N": str(data.ttl_expire_at)},
        },
    )


def send_verify_email(ctx: ApplicationContext, email: str, verify_token: str) -> None:
    cfg = ctx.config
    subject = "【AlkNote】本人確認のお願い"
    body = (
        "以下のURLをクリックして本人確認を完了してください。\n\n"
        f"https://example.com/verify?token={verify_token}\n\n"
        "このURLは１時間有効です。"
    )

    msg = MIMEMultipart()
    msg["From"] = cfg.GMAIL_APP_USER_NAME
    msg["To"] = email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP(cfg.GMAIL_HOST, cfg.GMAIL_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(cfg.GMAIL_APP_USER_NAME, cfg.GMAIL_APP_PASSWORD)
        server.sendmail(cfg.GMAIL_APP_USER_NAME, email, msg.as_string())
