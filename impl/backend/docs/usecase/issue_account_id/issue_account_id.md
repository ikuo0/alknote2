# アカウント作成-アカウント発行
- 概要
  - トークンを検証
  - アカウントを発行
  - ログインURLをメール送信
- 処理
  - ddbVerifyToken より検証トークンを取得する
    - トークンの有効性を確認する
  - account_id("aid.{unixtime(ms)}.{uuid4}.{uuid4}") を発行する
    - ddbAccount にアカウント情報を保存する
    - ddbVerifyToken のレコードは削除する
  - メール送信処理

# 作成条件:
- リソース定義は impl/backend/docs/resource_design.md の内容に従う
- impl/backend/src/modules/usecase/issue_account_id/usecase.py として作成
- impl/backend/src/modules/usecase/issue_account_id/ 以下にソースを収める、上層ディレクトリを参照しない
- コードファイル構成は以下に従い、追加ファイルは作成しない
- コードルール:
  - 主処理: usecase.py → service.py の機能を並べて呼ぶだけ
  - 各機能: service.py
  - データアクセス: repository.py
  - データクラス: model.py
  - 他業務で流用しそうな機能: public.py, 流用可能そうな機能が無い場合は空で良い
- domain.py, misc.py, util.py, db.py などの追加ファイルは作成しない
- service.py にまとめて実装する
- service.py は肥大化して構わない
- usecase, service に記載されるすべての処理は ApplicationContext を引数に取る
- usecase, service に記載されるすべての処理は ApplicationContext.info/warning/error でログを残す
- usecase, service に記載されるすべての処理は ApplicationContext.config を参照し処理を記載する
- ApplicationContext インスタンス作成は API Router や バッチ処理側で行うため、usecase, service では行わない、引数で受け取るだけ。
- impl/backend/src/modules/helper/helper.py に記載されている機能は service.py で呼び出しても良い
- import 文は src.modules. から始まる形で記載する

# 処理の流れ

## 入力処理
- 入力パラメータ
  - verify_token: string, required
- 処理
  - verify_token をキーに ddbVerifyToken からデータ取得
    - データが存在しない場合、tracebackログを残し raise "InvalidTokenError" する
- 正常終了時
  - 取得したデータを全て返却する

## 主処理
- 入力パラメータ
  - password: string, required, 4桁の数字
  - stored_email: string, required
  - stored_password_hash: string, required
  - stored_attempts: int, required
  - stored_expiry_utms: int, required
- 処理
  - stored_attempts 確認
    - 3以上の場合、tracebackログを残し raise "TooManyAttemptsError" する
  - password 正当性確認
    - stored_expiry_utms と現在のUNIXTIME(s) を比較してトークンの有効期限を確認する
      - 期限切れの場合、tracebackログを残し raise "TokenExpiredError" する
    - stored_password_hash と password を比較して確認する
      - 不正時
        - stored_attempts を 1 増やして ddbVerifyToken に保存する
        - tracebackログを残し raise "InvalidPasswordError" する
  - 出力用の値を作成する
    - account_id: "aid.{unixtime(ms)}.{uuid4}.{uuid4}"
    - instance_id: "iid.{unixtime(ms)}.{uuid4}"
    - email: stored_email
    - attempts: stored_attempts
    - email_hash: stored_email をハッシュ化した値
    - create_utms: 現在のUNIXTIME(ms)
    - billing_utms: 現在のUNIXTIME(ms)
    - expiry_utms: 現在のUNIXTIME(ms) + Config.INITIAL_EXTENSION_UTMS
    - reverify_due_utms: 現在のUNIXTIME(ms) + Config.REVERIFY_INTERVAL_UTMS
    - ttl_expire_at: 現在のUNIXTIME(s) + Config.LIFE_TIME_UTMS / 1000
  - 正常終了時
    - 出力用の値を返却する

## 出力処理
  - 入力パラメータ
    - verify_token: string, required
    - account_id: string, required
    - instance_id: string, required
    - email: string, required
    - email_hash: string, required
    - create_utms: int, required
    - billing_utms: int, required
    - expiry_utms: int, required
    - reverify_due_utms: int, required
    - ttl_expire_at: int, required
  - 処理
    - DB操作
      - ddbAccount に値を保存する
      - ddbInstance に値を保存する
      - ddbVerifyToken のレコードを削除する
      - 例外時、tracebackログを残し raise "DatabaseError" する
        - ttl_expire_at を設定してあるのでレコード削除されるので、トランザクション処理は不要
    - メール送信処理
      - 送信先: 入力メールアドレス
      - タイトル: "【AlkNote】アカウント発行のお知らせ"
      - 本文: "以下のURLをクリックしてサインインしてください。\n\nhttps://example.com/signin?aid={account_id}"
  - 正常終了時
    - なし
