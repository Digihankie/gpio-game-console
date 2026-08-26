# Thor：雙助理語音 → 一小段 Dify → 機器狗夾送

Reachy 是**現地**個人助理，K10 是**隨身**個人助理。兩者都只做語音入口。  
指令進 Thor 之後，Dify 只跑**一小段** Chatflow（抽出要拿什麼、送到哪、給誰），再交給 Thor 的 Nvidia 底層找物，叫機器狗去夾、送到人面前。

```text
Reachy 語音（現地） ─┐
                    ├─ Thor ASR（已有 Whisper / SenseVoice）
K10 語音（隨身）   ─┘
                    ↓
              Dify Chatflow（Start → LLM → Answer）
                    ↓  {item, dest, recipient, confirm, say}
              dispatcher :8766
                    ↓ confirm=true → K10 按 A
              Nvidia VLM 在狗鏡頭上找物品
                    ↓
              Dogzilla：走到 → 夾 → 送到 → 放下
                    ↓
              回原助理播報（Reachy 說 / K10 顯示）
```

不要再裝第二套 Dify，也不要再載一份大模型。Chatflow 選 Thor 現有 Nvidia endpoint。

## Dify 就這一段

三個節點，沒有 Code / Agent / RAG：

`Start → LLM → Answer`

契約：

```json
{
  "intent": "fetch",
  "item": "紅色馬克杯",
  "dest": "客廳茶几",
  "recipient": "Hank",
  "confirm": true,
  "say": "機器狗去把紅色馬克杯送到客廳給 Hank"
}
```

`fetch` 一律 `target=dogzilla` 且必須等 K10 A。缺欄位就請人再說一次，不會放狗。

## 目錄

| 路徑 | 用途 |
|---|---|
| `dify/fleet-dispatch.dify.yml` | 匯入 Thor Dify 的取物 Chatflow |
| `dify/SYSTEM.md` | 同一份 System Prompt |
| `dispatcher/` | `/voice` 入口、確認閘、VLM + 狗的 call 對照 |
| `hermes-skill/ask_dify_dispatch/` | Reachy / Hermes 聽到後呼叫 |
| `k10/confirm.py` | 隨身助理：顯示拿／到／給，A 出發 |
| `scripts/send_voice.py` | 本機模擬兩種助理的語音文字 |

## 在 Thor 上接

```bash
cd thor-dify-openclaw
./scripts/install-on-thor.sh
# 開 :3080 匯入 DSL，LLM 選 Thor 地端模型，複製 API Key
cp .env.example .env
docker compose up -d
docker restart hermes-agent

python3 scripts/send_voice.py --source reachy "把桌上的紅色馬克杯拿到客廳茶几給 Hank"
python3 scripts/send_voice.py --source k10 "把遙控器送到沙發給媽媽"
```

Hermes 現場路徑：`reachy_listen` 得到文字後跑 `ask_dify.py --source reachy "..."`。  
K10 板上 ASR 弱，正式是把短語交給 Thor ASR，再 `POST /voice {"source":"k10","text":"..."}`。

`DRY_RUN=1`（預設）只規劃 `calls`。`dogzilla_*` 對 Thor `/home/hank/docker/fleet/dogzilla_mcp`；還沒接進 Hermes 時，核准後仍看得到完整步驟，不會真的放狗。

## 本機測驗

```bash
cd thor-dify-openclaw
python3 -m unittest discover -s dispatcher -v
```
