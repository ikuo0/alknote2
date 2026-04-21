# アカウント作成-本人検証
- 概要
  - メールアドレスと4桁パスワードを受け取って
  - マジックリンクの付いたメールを送信する
- 処理
  - ddbVerifyToken に検証トークンを保存する
  - AWS SES によるメール送信
    - ※ただし開発期間中は個人の GMAIL APP でメール送信する

# 作成条件:
- リソース定義は impl/backend/docs/resource_design.md の内容に従う
- impl/backend/src/modules/usecase/signup/signup_verify_identity/usecase.py として作成
- impl/backend/src/modules/usecase/signup/signup_verify_identity/ 以下にソースを収める、上層ディレクトリを参照しない
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
- pass

## 主処理
- 入力パラメータ
  - email: string, required
  - password: string, required, 4桁の数字
- 処理
  - email 正当性確認
    - 不正時、tracebackログを残し raise "InvalidEmailError" する
  - password 正当性確認
    - 不正時、tracebackログを残し raise "InvalidPasswordError" する
  - ddbVerifyToken 用の値作成
    - verify_token: "vtoken.{unixtime(ms)}.{uuid4}"
    - email: 入力値
    - password_hash: パスワードをハッシュ化した値
    - attempts: 0
    - create_utms: 現在のUNIXTIME(ms)
    - expiry_utms: 現在のUNIXTIME(s) + Config.VTOKEN_LIFETIME_UTMS / 1000
    - ttl_expire_at: 現在のUNIXTIME(s) + Config.VTOKEN_LIFETIME_UTMS / 1000
  - 正常終了時
    - ddbVerifyToken 用の値を返却する

## 出力処理
  - 入力パラメータ
    - verify_token: "vtoken.{unixtime(ms)}.{uuid4}"
    - email: 入力値
    - password_hash: 入力値
    - attempts: 0
    - create_utms: 入力値
    - expiry_utms: 入力値
    - ttl_expire_at: 入力値
  - 処理
    - ddbVerifyToken に値を保存する
    - メール送信処理
      - 送信先: 入力メールアドレス
      - タイトル: "【AlkNote】本人確認のお願い"
      - 本文: "以下のURLをクリックして本人確認を完了してください。\n\nhttps://example.com/verify?token={verify_token}\n\nこのURLは１時間有効です。"
  - 正常終了時
    - なし
