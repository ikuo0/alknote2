#!/usr/bin/env bash

trap 'kill $(jobs -p) 2>/dev/null' INT TERM

set -u

cd "$(dirname "$0")"

# DynamoDB
( cd impl/backend/local_environ/dynamodb && docker-compose up ) &

# backend
source .venv/bin/activate
export APP_ENV=local
export PYTHONPATH=impl/backend
export AWS_ACCESS_KEY_ID=dummy
export AWS_SECRET_ACCESS_KEY=dummy
export AWS_DEFAULT_REGION=ap-northeast-1
unset AWS_SESSION_TOKEN

set -a
source .secret/env.sh
set +a

uvicorn impl.backend.src.fastapi_app.main:app --host 0.0.0.0 --port 3000 --reload &


# front
python3 -m http.server 5173 --directory impl/frontend/src &

# 前面に残してログを見る（Ctrl+C で止める）
# wait

# httpd 等、ポートを使ったプロセスが残っている時の対応
# PIDを調べる
# lsof -i :5173
# lsof -i :3000
# lsof -i :8000
# lsof -i :5173,3000,8000
# PIDを指定して kill する
# kill -9 <PID>

# http://localhost:5173/ でフロントエンド
# http://localhost:3000/ でバックエンド