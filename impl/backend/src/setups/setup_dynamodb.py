"""
DynamoDB テーブルセットアップスクリプト
resource_design.md に定義された全テーブルを作成する

使用方法:
  python -m impl.backend.src.setups.setup_dynamodb          # テーブル作成
  python -m impl.backend.src.setups.setup_dynamodb reset    # 既存テーブルを削除してから作成
"""

import sys
import boto3
from botocore.exceptions import ClientError

from src.modules.config.config import Config, LocalConfig


TABLES = [
    {
        "TableName": "ddbAccount",
        "KeySchema": [
            {"AttributeName": "account_id", "KeyType": "HASH"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "account_id", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "ddbInstance",
        "KeySchema": [
            {"AttributeName": "instance_id", "KeyType": "HASH"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "instance_id", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "ddbVerifyToken",
        "KeySchema": [
            {"AttributeName": "verify_token", "KeyType": "HASH"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "verify_token", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "ddbAccessToken",
        "KeySchema": [
            {"AttributeName": "access_token", "KeyType": "HASH"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "access_token", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
]


def get_dynamodb_client(cfg: Config):
    return boto3.client(
        "dynamodb",
        region_name=cfg.DDB_REGION,
        endpoint_url=f"http://{cfg.DDB_HOST}",
        aws_access_key_id=cfg.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=cfg.AWS_SECRET_ACCESS_KEY,
    )


def delete_table(client, table_name: str):
    try:
        client.delete_table(TableName=table_name)
        waiter = client.get_waiter("table_not_exists")
        waiter.wait(TableName=table_name)
        print(f"[削除完了] {table_name}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            print(f"[スキップ] {table_name} は存在しません")
        else:
            raise


def create_table(client, table_def: dict):
    table_name = table_def["TableName"]
    try:
        client.create_table(**table_def)
        waiter = client.get_waiter("table_exists")
        waiter.wait(TableName=table_name)
        print(f"[作成完了] {table_name}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"[スキップ] {table_name} は既に存在します")
        else:
            raise


def main():
    reset = len(sys.argv) > 1 and sys.argv[1] == "reset"

    cfg = LocalConfig()
    client = get_dynamodb_client(cfg)

    if reset:
        print("=== テーブルをリセットします ===")
        for table_def in TABLES:
            delete_table(client, table_def["TableName"])

    print("=== テーブルを作成します ===")
    for table_def in TABLES:
        create_table(client, table_def)

    print("=== セットアップ完了 ===")


if __name__ == "__main__":
    main()
