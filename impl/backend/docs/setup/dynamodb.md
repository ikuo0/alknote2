# DynamoDB のセットアップ
impl/backend/src/setups/setup_dynamodb.py を作成
impl/backend/docs/resource_design.md の Type: DynamoDB と記載のあるテーブルを全て作成するスクリプトを実装する
ddbInstance 等のタイトルをそのままテーブル名とする
引数に reset とあった場合には既存テーブルを削除してから作成するようにする
