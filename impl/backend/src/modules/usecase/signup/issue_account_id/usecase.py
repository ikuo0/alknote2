from src.modules.application.application import ApplicationContext
from impl.backend.src.modules.usecase.signup.issue_account_id.model import IssuedAccountData
from impl.backend.src.modules.usecase.signup.issue_account_id import service


def execute(ctx: ApplicationContext, verify_token: str, password: str) -> IssuedAccountData:
    ctx.info("issue_account_id usecase 開始")

    # 入力処理: ddbVerifyToken からデータ取得
    stored = service.fetch_verify_token_data(ctx, verify_token)

    # 主処理: 検証 & アカウントデータ作成
    data = service.verify_and_create_account_data(ctx, password, stored)

    # 出力処理: DB保存 & メール送信
    service.save_and_notify(ctx, verify_token, data)

    ctx.info("issue_account_id usecase 完了")
    return data
