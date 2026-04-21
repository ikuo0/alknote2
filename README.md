
# pytyhon 環境構築
```bash
pytyhon -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

# git
```bash
# git config --global credential.helper "cache --timeout=3600"
git remote set-url origin git@github.com:ikuo0/alknote2.git
```

# setup backend environ

setup_local_env.sh サンプル

```bash
source .venv/bin/activate
export APP_ENV=local
export PYTHONPATH=/workspaces/alknote2/impl/backend
export AWS_ACCESS_KEY_ID=dummy
export AWS_SECRET_ACCESS_KEY=dummy
export AWS_DEFAULT_REGION=ap-northeast-1
unset AWS_SESSION_TOKEN

set -a
source .secret/env.sh
set +a
```

## .secret/env.sh について
次のような内容を記載してください

```bash
TEST_SENDER_EMAIL="abcg@gmail.com"
GMAIL_APP_USER_NAME="abc@gmail.com"
GMAIL_APP_PASSWORD="???? eeee vvvv kkkk"
```
