

- ddbAccount
  - Type: DynamoDB
  - Table: On-demand
  - Fields
    - account_id: hash_key, string, "aid.{unixtime(ms)}.{uuid4}.{uuid4}"
    - instance_id: string
    - email_hash: string
    - create_utms: int
    - billing_utms: int, 課金開始日時、初期値はcreate_utmsと同じ値を設定する
    - expiry_utms: int, 7日後などの有効期限
    - reverify_due_utms: int, 再検証期限、設定値に従い設定する
    - ttl_expire_at: int, DynamoDBのTTL機能で自動削除するためのフィールド。UNIXTIME(秒) 、 expiry_utms + 設定値に従った値を設定する
  - Relations
    - _
  - Note: account_id is unique across all instances, so it can be used as a global identifier for accounts.
  - Note: utms は UNIXTIME(ミリ秒) を指す

- ddbInstance
  - Type: DynamoDB
  - Table: On-demand
  - Fields
    - instance_id: hash_key, string, "iid.{unixtime(ms)}.{uuid4}"
    - account_id: string
    - create_utms: int
    - ttl_expire_at: int, DynamoDBのTTL機能で自動削除するためのフィールド。UNIXTIME(秒) 、 expiry_utms + 設定値に従った値を設定する
  - Relations
    - this.instance_id -> ddbAccount.instance_id

- ddbVerifyToken
  - Type: DynamoDB
  - Table: On-demand
  - Fields
    - verify_token: hash_key, string, "vtoken.{unixtime(ms)}.{uuid4}"
    - email: string
    - password_hash: string
    - attempts: int, default: 0, 3回間違えたら検証拒否
    - create_utms: int
    - expiry_utms: int, 30分後などの有効期限
    - ttl_expire_at: int, DynamoDBのTTL機能で自動削除するためのフィールド。UNIXTIME(秒) 、 create_utms + 12時間
  - Relations
  - _
  - Note: あるアカウントに対する検証トークン。マジックリンク等で検証する際に使用する

- ddbAccessToken
  - Type: DynamoDB
  - Table: On-demand
  - Fields
    - access_token: hash_key, string, "atoken.{unixtime(ms)}.{uuid4}"
    - instance_id: string
    - create_utms: int
    - expiry_utms: int, 7日後などの有効期限
    - ttl_expire_at: int, DynamoDBのTTL機能で自動削除するためのフィールド。UNIXTIME(秒) 、 expiry_utms + 設定値に従った値を設定する
  - Relations
    - this.instance_id -> ddbInstance.instance_id
  - Note: あるインスタンスに対するアクセス権限を管理するトークン

