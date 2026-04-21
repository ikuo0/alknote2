export APP_ENV=local
export PYTHONPATH=/workspaces/alknote2/impl/backend
export AWS_ACCESS_KEY_ID=dummy
export AWS_SECRET_ACCESS_KEY=dummy
export AWS_DEFAULT_REGION=ap-northeast-1
unset AWS_SESSION_TOKEN

source .venv/bin/activate

set -a
source .secret/env.sh
set +a
