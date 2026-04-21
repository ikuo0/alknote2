import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import boto3

from src.modules.application.application import ApplicationContext
from impl.backend.src.modules.usecase.signup.issue_account_id.model import StoredVerifyTokenData, IssuedAccountData


def _make_ddb_client(ctx: ApplicationContext):
    cfg = ctx.config
    return boto3.client(
        "dynamodb",
        region_name=cfg.DDB_REGION,
        endpoint_url=f"http://{cfg.DDB_HOST}",
        aws_access_key_id=cfg.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=cfg.AWS_SECRET_ACCESS_KEY,
    )


def get_verify_token(ctx: ApplicationContext, verify_token: str) -> dict | None:
    client = _make_ddb_client(ctx)
    resp = client.get_item(
        TableName="ddbVerifyToken",
        Key={"verify_token": {"S": verify_token}},
    )
    return resp.get("Item")


def increment_attempts(ctx: ApplicationContext, verify_token: str, new_attempts: int) -> None:
    client = _make_ddb_client(ctx)
    client.update_item(
        TableName="ddbVerifyToken",
        Key={"verify_token": {"S": verify_token}},
        UpdateExpression="SET attempts = :a",
        ExpressionAttributeValues={":a": {"N": str(new_attempts)}},
    )


def save_account(ctx: ApplicationContext, data: IssuedAccountData) -> None:
    client = _make_ddb_client(ctx)
    client.put_item(
        TableName="ddbAccount",
        Item={
            "account_id": {"S": data.account_id},
            "instance_id": {"S": data.instance_id},
            "email_hash": {"S": data.email_hash},
            "create_utms": {"N": str(data.create_utms)},
            "billing_utms": {"N": str(data.billing_utms)},
            "expiry_utms": {"N": str(data.expiry_utms)},
            "reverify_due_utms": {"N": str(data.reverify_due_utms)},
            "ttl_expire_at": {"N": str(data.ttl_expire_at)},
        },
    )


def save_instance(ctx: ApplicationContext, data: IssuedAccountData) -> None:
    client = _make_ddb_client(ctx)
    client.put_item(
        TableName="ddbInstance",
        Item={
            "instance_id": {"S": data.instance_id},
            "account_id": {"S": data.account_id},
            "create_utms": {"N": str(data.create_utms)},
            "ttl_expire_at": {"N": str(data.ttl_expire_at)},
        },
    )


def delete_verify_token(ctx: ApplicationContext, verify_token: str) -> None:
    client = _make_ddb_client(ctx)
    client.delete_item(
        TableName="ddbVerifyToken",
        Key={"verify_token": {"S": verify_token}},
    )


def send_account_email(ctx: ApplicationContext, email: str, account_id: str) -> None:
    cfg = ctx.config
    subject = "【AlkNote】アカウント発行のお知らせ"
    body = (
        "以下のURLをクリックしてサインインしてください。\n\n"
        f"https://example.com/signin?aid={account_id}"
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
