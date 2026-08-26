# Thor Hermes / OpenClaw 加上 Dify

Thor 上 **Dify 已經在跑**（`/home/hank/docker/dify/docker`，nginx `:3080`）。這裡補的是缺的那一層：

```text
人講中文
    → Hermes skill ask_dify_dispatch
        → Dify Chatflow（只出 JSON）
            → dispatcher :8766
                → confirm=false：回 Reachy MCP calls 給 Hermes 執行
                → confirm=true ：等 K10 按 A / B
```

不要再裝第二套 Dify，也不要再載一份大模型。Chatflow 選 Thor 現有的地端 endpoint。

## 目錄

| 路徑 | 用途 |
|---|---|
| `dify/fleet-dispatch.dify.yml` | 匯入 Thor Dify 的 Chatflow |
| `dify/SYSTEM.md` | 同一份 System Prompt（手動貼也可以） |
| `dispatcher/` | 規劃 / 確認閘 / Reachy call 對照 |
| `hermes-skill/ask_dify_dispatch/` | 複製進 Hermes skills |
| `k10/confirm.py` | 行空板現場 A/B |
| `docker-compose.yml` | 只起 `dify-dispatch`（host network） |

## JSON 契約

```json
{
  "target": "reachy",
  "intent": "greet",
  "confirm": true,
  "say": "大家好，我是 Reachy"
}
```

| target | 現況 |
|---|---|
| `reachy` | 已對到 `reachy_*` MCP tools |
| `k10` | 顯示 + 確認閘 |
| `m3` / `dogzilla` | enum 預留；`demo` 會改成 K10 顯示「尚未接入」 |
| Crazyflie | 直接擋 |

`greet` / `demo` 即使模型漏標 `confirm`，dispatcher 也會改成等 K10。

## 在 Thor 上接

```bash
# 1. 這份 repo 放到 Thor 後
cd thor-dify-openclaw
./scripts/install-on-thor.sh

# 2. 瀏覽器開 Dify
#    http://192.168.8.195:3080 或 https://thor-mc.asingular.ai 旁邊那套 :3080
#    工作室 → 匯入 DSL → fleet-dispatch.dify.yml
#    LLM 節點選 Thor 地端模型 → 發佈 → API Access 複製 Key

# 3. 起 bridge（不要動現有 dify / langgraph-api compose）
cp .env.example .env
# 編輯 .env 填 DIFY_API_KEY
docker compose up -d

curl -s http://127.0.0.1:8766/health
docker restart hermes-agent
python3 hermes-skill/ask_dify_dispatch/scripts/ask_dify.py "請 Reachy 說午安"
```

`DRY_RUN=1`（預設）只規劃 `calls`，不自己打 Reachy。Hermes 依 `calls` 去呼 `:9000`。現場要 dispatcher 代打時再把 `DRY_RUN=0`（仍建議先走 Hermes）。

## 本機測驗（不需要 Thor）

```bash
cd thor-dify-openclaw
python3 -m unittest discover -s dispatcher -v
```
