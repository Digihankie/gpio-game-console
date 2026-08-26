#!/usr/bin/env bash
# 在 Thor 上：複製 Hermes skill，並提示如何掛 dispatcher。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HERMES_SKILLS="${HERMES_SKILLS:-/home/hank/docker/langgraph-api/.openclaw/hermes/skills}"
DEST="${HERMES_SKILLS}/ask_dify_dispatch"

mkdir -p "$HERMES_SKILLS"
rm -rf "$DEST"
cp -a "$ROOT/hermes-skill/ask_dify_dispatch" "$DEST"
chmod +x "$DEST/scripts/ask_dify.py"

echo "copied Hermes skill → $DEST"
echo
echo "下一步（在 Thor）："
echo "  1. 開 http://127.0.0.1:3080 匯入 $ROOT/dify/fleet-dispatch.dify.yml"
echo "  2. Chatflow 選 Thor 已有的 Nvidia 地端模型，建立 API Key"
echo "  3. cd $ROOT && cp .env.example .env && 填 DIFY_API_KEY"
echo "  4. docker compose up -d"
echo "  5. curl -s http://127.0.0.1:8766/health"
echo "  6. docker restart hermes-agent   # 讓 skill 進容器"
echo "  7. 把 k10/confirm.py 的 THOR 改成這台 LAN IP 後燒進 K10"
echo "  8. 試：python3 $ROOT/scripts/send_voice.py --source reachy '把桌上馬克杯送到客廳給 Hank'"
