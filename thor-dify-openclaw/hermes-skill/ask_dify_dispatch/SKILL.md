---
name: ask_dify_dispatch
description: 把 Reachy 或 K10 聽到的取物指令交給 Dify 一小段 Chatflow，抽出物品／地點／對象，再讓 Thor 叫機器狗去夾送。
---

# Ask Dify Dispatch（取物）

Reachy = 現地個人助理，K10 = 隨身個人助理。兩者都只做**語音入口**。  
Dify 只做**一小段規劃**。夾、走、放是 **Dogzilla + Thor Nvidia VLM**。

聽到「拿／夾／送／給誰」時先跑這個 skill，不要自己猜路點。

## 怎麼跑

```bash
python3 "$HERMES_HOME/skills/ask_dify_dispatch/scripts/ask_dify.py" --source reachy "把桌上馬克杯送到客廳給 Hank"
python3 "$HERMES_HOME/skills/ask_dify_dispatch/scripts/ask_dify.py" --source k10 "把遙控器拿到沙發給媽媽"
```

`--source` 必須是聽到語音的那一個助理：`reachy` 或 `k10`。

環境變數：`DIFY_DISPATCH_URL`（預設 `http://127.0.0.1:8766`）。

## Hermes 聽到語音之後

1. Reachy：`reachy_listen`（或 Thor Whisper / SenseVoice）得到文字。
2. K10：板上把文字 POST 到 `/voice`，或 Hermes 收到後帶 `--source k10`。
3. 跑這個 script。
4. 看 stdout：

| `status` | 要做的事 |
|---|---|
| `awaiting_confirm` | **機器狗先別動**。K10 顯示物品／地點／對象，A 才走。 |
| `ready` | 依序執行 `calls`：`nvidia_vlm_locate` → `dogzilla_goto` → `dogzilla_grasp` → `dogzilla_goto` → `dogzilla_release` → 回原助理播報。 |
| `denied` / `expired` | 中止。 |

`nvidia_vlm_locate` 打 Thor 已有的地端 VLM（狗的鏡頭或現場相機），不要另開雲端模型。

## 不要做

- 不要讓 Reachy 或 K10 去夾東西。
- 不要為 Dify 再載一份 LLM；Chatflow 共用 Thor Nvidia endpoint。
- 不要接 Crazyflie。
