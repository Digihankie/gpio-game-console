---
name: ask_dify_dispatch
description: 把自然語言交給 Thor 上的 Dify Chatflow，拿到艦隊調度 JSON，再依 confirm 決定立刻執行或等 K10 A/B。
---

# Ask Dify Dispatch

當使用者要用中文指揮 Reachy / K10 /（預留）M3 / Dogzilla 時，**先跑這個 skill**，不要自己猜 tool。

Dify 只負責規劃。真正執行仍是 Hermes：把回傳的 `calls` 轉成 MCP / 既有 tool。

## 怎麼跑

在 Thor 上 dispatcher 預設聽 `127.0.0.1:8766`。

```bash
python3 /opt/data/skills/ask_dify_dispatch/scripts/ask_dify.py "請 Reachy 跟大家打招呼"
```

若 skill 被複製到 Hermes home：

```bash
python3 "$HERMES_HOME/skills/ask_dify_dispatch/scripts/ask_dify.py" "$USER_TEXT"
```

環境變數：

- `DIFY_DISPATCH_URL`（預設 `http://127.0.0.1:8766`）
- 或直接打 Dify：`DIFY_API_URL`、`DIFY_API_KEY`

## 回傳怎麼用

stdout 是 JSON。

| `status` | Hermes 要做的事 |
|---|---|
| `ready` | 依序呼叫 `calls[].tool`。`reachy_*` 走 Reachy MCP `:9000`。`k10_display` 只把 `say` 講出來／留給 K10 顯示。 |
| `awaiting_confirm` | **不要動機器人**。告訴使用者看 K10：A 核准、B 拒絕。之後可再 `POST /confirm` 或等 dispatcher 被 K10 解鎖。 |
| `denied` / `expired` | 中止，不要補跑動作。 |

危險動作（揮手、跳舞、問候動起來）即使 Dify 漏標 `confirm`，dispatcher 也會改成 `awaiting_confirm`。

## 不要做

- 不要把 `target=m3` / `dogzilla` 的 `demo` 真的往車上丟；bridge 會改成 K10 顯示「尚未接入」。
- 不要接受 Crazyflie / 起飛；bridge 會擋。
- 不要為了作業再載一份大模型。Dify 與 Hermes 共用 Thor 已有的地端 endpoint。
