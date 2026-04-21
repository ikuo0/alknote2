from src.modules.application.application import ApplicationContext
from src.modules.usecase.signup_verify_identity.model import VerifyTokenData
from src.modules.usecase.signup_verify_identity import service


def execute(ctx: ApplicationContext, email: str, password: str) -> VerifyTokenData:
    ctx.info("signup_verify_identity usecase 開始")

    # 入力バリデーション
    service.validate_email(ctx, email)
    service.validate_password(ctx, password)

    # ddbVerifyToken 用データ作成
    data = service.create_verify_token_data(ctx, email, password)

    # 出力処理: DB保存 & メール送信
    service.save_verify_token(ctx, data)
    service.send_verify_email(ctx, email, data.verify_token)

    ctx.info("signup_verify_identity usecase 完了")
    return data
