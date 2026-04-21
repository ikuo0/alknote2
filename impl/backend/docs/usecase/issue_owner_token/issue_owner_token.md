# トークン発行-オーナートークンの発行
- 概要
  - account_id 認証をする
  - オーナーアクセストークンを発行する
- 処理
  - ddbAccount より account_id をキーにレコードを取得する
    - 期限切れ等を確認して、発行可能か確認する
  - access_token を発行する
  - サインインURL(access_token付き)の記載されたメールを送信する

# 作成条件:
- リソース定義は impl/backend/docs/resource_design.md の内容に従う
- impl/backend/src/modules/usecase/issue_owner_token/usecase.py として作成
- impl/backend/src/modules/usecase/issue_owner_token/ 以下にソースを収める、上層ディレクトリを参照しない
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
  - account_id: string, required
- 処理
  - account_id をキーに ddbAccount からデータ取得
    - データが存在しない場合、tracebackログを残し raise "InvalidAccountError" する
  - instance_id をキーに ddbInstance からデータ取得
    - データが存在しない場合、tracebackログを残し raise "InvalidAccountError" する
- 正常終了時
  - 次のデータを返却する
    - account_id: string
    - instance_id: string
    - expiry_utms: int
    - reverify_due_utms: int

## 主処理
- 入力パラメータ
  - account_id: string, required
  - instance_id: string, required
  - expiry_utms: int, required
  - reverify_due_utms: int, required
- 処理
  - expiry_utms 期限内であれば、"owner" 権限を持つトークンを発行する
  - expiry_utms + Config.BILLING_GRACE_UTMS 期限内であれば、"expired_owner" 権限を持つトークンを発行する
  - reverify_due_utms 期限を超えているか確認する
    - 超えている場合、tracebackログを残し raise "ReverificationRequiredError" する
    - 3以上の場合、tracebackログを残し raise "TooManyAttemptsError" する
  - expiry_utms + Config.BILLING_GRACE_UTMS 期限を超えている場合は raise "AccountUnavailableError" する
  - access_token を発行する
    - access_token = "atoken.{unixtime(ms)}.{uuid4}"
  - 出力用の値を作成する
    - access_token: "atoken.{unixtime(ms)}.{uuid4}"
    - instance_id: 入力の instance_id をそのまま使用
    - create_utms: 現在のUNIXTIME(ms)
    - expiry_utms: 現在のUNIXTIME(ms) + Config.ATOKEN_DEFAULT_LIFETIME_UTMS
    - ttl_expire_at: 現在のUNIXTIME(s) + Config.ATOKEN_DEFAULT_LIFETIME_UTMS / 1000
  - 正常終了時
    - 出力用の値を返却する

## 出力処理
  - 入力パラメータ
    - access_token: string, required
    - instance_id: string, required
    - create_utms: int, required
    - expiry_utms: int, required
    - ttl_expire_at: int, required
  - 処理
    - DB操作
      - ddbAccessToken に値を保存する
      - 例外時、tracebackログを残し raise "DatabaseError" する
        - ttl_expire_at を設定してあるのでレコード削除されるので、トランザクション処理は不要
    - メール送信処理
      - 送信先: 入力メールアドレス
      - タイトル: "【AlkNote】サインインURLのお知らせ"
      - 本文: "以下のURLをクリックしてサインインしてください。\n\nhttps://example.com/signin?atoken={access_token}"
  - 正常終了時
    - なし
