#!/usr/bin/env bash
# 一键部署 / 升级脚本（Linux）
#
# 第一次部署：
#   sudo mkdir -p /opt/zhaopin && sudo chown $USER:$USER /opt/zhaopin
#   git clone https://github.com/shanglily01-lab/zhaopin.git /opt/zhaopin
#   cd /opt/zhaopin && cp .env.example .env && vim .env   # 填真实凭据
#   bash deploy/deploy.sh
#
# 后续升级（拉新代码 -> 装依赖 -> 重启服务）：
#   cd /opt/zhaopin && bash deploy/deploy.sh

set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${APP_DIR}/.venv"
SERVICE_NAME="zhaopin"

cd "${APP_DIR}"

echo "[1/5] pull latest code"
if [ -d .git ]; then
    git pull --ff-only
fi

echo "[2/5] ensure virtualenv at ${VENV}"
if [ ! -d "${VENV}" ]; then
    python3 -m venv "${VENV}"
fi
# shellcheck source=/dev/null
source "${VENV}/bin/activate"

echo "[3/5] install python deps"
pip install --upgrade pip wheel
pip install -r requirements.txt

echo "[4/5] verify .env exists"
if [ ! -f "${APP_DIR}/.env" ]; then
    echo "ERROR: ${APP_DIR}/.env not found. cp .env.example .env and fill in the values." >&2
    exit 1
fi

echo "[5/5] (re)start service"
if systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
    sudo systemctl restart "${SERVICE_NAME}"
    sudo systemctl status "${SERVICE_NAME}" --no-pager | head -n 12
else
    echo "WARN: systemd unit ${SERVICE_NAME}.service not installed yet."
    echo "      run: sudo cp deploy/${SERVICE_NAME}.service /etc/systemd/system/"
    echo "           sudo systemctl daemon-reload && sudo systemctl enable --now ${SERVICE_NAME}"
fi

echo "done."
