# 幕後花絮：技術含金量怎麼講、怎麼拍

正片 2:42 先讓一只假飛鴿急報把快馬騙去夾龍眼，貴妃念完《過華清宮》，再讓真飛鴿與 YOLO 改正。  
花絮把**為什麼第一趟會錯、第二趟才準**講完：急報是未核驗情報，龍眼是仿冒物。唐朝換的是馬，我們換的是 **Jetson 上的感知與調度**。

K10 不跑大模型。它是隨身探子與準奏板；腦子在 **NVIDIA Jetson AGX Thor + JetPack 7**。

---

## 一、一句總表（對外）

| 劇中 | 技術 | 跑在哪 | 花絮怎麼拍 |
|---|---|---|---|
| 驛丞的算盤 | JetPack 7、CUDA、TensorRT、本機 LLM／VLM | Thor | 機櫃燈、`nvidia-smi`／jtop 一閃 |
| 聖旨三欄 | Dify Chatflow（Start→LLM→Answer） | Thor `:3080` | 螢幕只出 item／dest／recipient |
| 假急報 | `intel=hearsay`；K10 黃字急報 | K10／道具帖 | 與第二趟綠字核驗對切，不拍真實郵件 |
| 驛站總管 | dispatcher：規劃 `calls[]` | Thor `:8766` | 終端出現取物步驟 |
| 宮門聽旨 | 4 Mic 陣列＋DOA＋STT | Reachy→Thor | 人說話，頭轉向聲源 |
| 掌事宣旨 | TTS（Azure／Kokoro／Riva） | Reachy | 「荔枝到了。」波形 |
| 認人 | YOLO＋臉部（Thor）；K10 板載人臉 | Thor／K10 | 框出人；K10 顯示 face id |
| 認荔 | YOLO-TRT＋VLM 找「荔枝盒」 | Thor | 偵測框打在盒子上 |
| 飛鴿傳書 | Crazyradio＋`cflib` 低空 scout | Thor 電台，不是 K10 | 手持電台＋起飛 |
| 雙闕定位 | Lighthouse 兩座燈塔＋機上 deck | 客廳兩角，覆蓋茶几／沙發 | 基座掃光、降落落在盒邊墊上 |
| 驛馬傳果 | Dogzilla MCP（MQTT／運動） | Thor `fleet` | topic 與狗起步同切 |
| 枝頭物候 | K10 溫濕度、光照、加速度 | 掛在「荔枝樹」旁 | 螢幕 T／RH／lux 變化 |
| 準奏 | K10 A／B | 現場閘 | 按 A 才 takeoff／grasp |
| 夢境 | ComfyUI／影像模型 | Thor GPU | 唐宮、嶺南、驛道出圖 |

---

## 二、還有哪些能進花絮（你們棧上已有）

比名單再多、而且**不必新買**：

1. **TensorRT YOLO**（`reachy-yolo-trt`）  
   正片裡盒子被夾，花絮給偵測框：`lychee_box`／`person`。這是 JetPack 7 上的加速，不是雲端 API。

2. **VLM 找物**（`nvidia_vlm_locate`／`reachy_describe_scene`）  
   飛鴿看完，Thor 用本機視覺語言模型回「盒子在茶几左側」。對上「枝頭有果」。

3. **聲源定向（DOA）**  
   Reachy 四麥不只錄音，還能轉頭對準開口的人。花絮用一條聲源箭頭疊畫面。

4. **雙路徑人臉**  
   - Thor／Reachy：`face_enroll`／`face_identify`（宮門驗身，誰准接荔）。  
   - K10：板載 `ai.face_recognize`（隨身探子在樹下確認來的是驛卒不是路人）。  
   貴妃正片是 AI 臉；花絮用**真人 stand-in 註冊**，講的是「驗的是權限，不是扮演貴妃」。

5. **Lighthouse 雙塔**  
   兩座 Bitcraze Lighthouse V2＋機上燈塔甲板。客廳對角架開，覆蓋茶几到沙發。  
   飛鴿有毫米級位姿，降落在荔枝盒旁放飛墊，不是目測飄落。  
   劇中：雙闕／烽燧把「枝頭」釘在座標系裡。花絮拍掃光、xyz 軌跡、落墊。

6. **MQTT 驛路**  
   Thor `mosquitto`：`lychee/scout`、`lychee/horse`、`lychee/climate`、`lychee/pose`。  
   花絮三分屏：publish → broker → 狗／鴿動。這就是古時換騎、換牒。

7. **K10 荔枝物候**（你點名的氣候）  
   掛在盆栽或戶外枝頭（或一盆替代「嶺南」）：  
   - AHT20：氣溫、濕度  
   - 光照：是否「日頭夠熟」  
   - 加速度：風大／有人碰樹 → 延後放飛  
   規則寫死給花絮看（示意即可）：  
   `T≥18°C` 且 `RH≥60%` 且 `lux 足夠` → 螢幕「枝頭已熟，準飛鴿」；否則「未熟，駁回」。  
   正片不必播公式，花絮播 5 秒曲線。

8. **K10 雙麥 → Thor STT**  
   隨身入口：板上錄短語，丟 Thor Whisper／SenseVoice。花絮對比「四麥宮門／雙麥探子」。

9. **確認閘 ≠ 聊天**  
   `fetch` 必 `confirm=true`。花絮把「模型建議」和「A 準奏」拆成兩格，這是作業要交的安全故事。

10. **MCP 工具鏈**  
   花絮捲過：`crazyflie_look` → `nvidia_vlm_locate` → `dogzilla_grasp`。聖旨短，驛卒步驟長。

11. **Docker Compose 分域**  
    Dify、dispatcher、fleet、ComfyUI 各是容器。花絮一眼 `docker compose ls`，講「驛館分曹，不共一廚」。

12. **本機推理、不出宮**  
    LLM／VLM／YOLO 都在 Thor。花絮強調沒有把貴妃語音送公有雲（TTS 若用 Azure 要老實講：聲可雲、決策在地）。

13. **Langfuse／MC 日誌**（若要給技術長看）  
    Mission Control 一條 activity：`pipelineId` 不必用，改疊「驛站日誌：scout ok / horse ok」。

**不要寫進花絮（會穿幫）**

- Dify 跑在 K10 上  
- Crazyflie 叼荔枝、空投  
- K10 當 Crazyradio 或 Lighthouse 地面站  
- 說飛鴿「看著落地」（落地靠燈塔座標，不是鏡頭伺服）  
- 再載一份搶顯存的大模型  

---

## 三、花絮短片分鏡（約 50 秒）

接在正片片尾之後，或作成片「製作特輯」。BGM：把〈紅塵主題〉改成極簡 click＋低頻，旁白改技術、慢、短。

| 鏡 | 時間 | 畫面 | 旁白（可燒字幕） | 技術點 |
|---|---|---|---|---|
| B01 | 0:00–0:05 | Thor 燈亮，JetPack／jtop | 「驛丞在 Thor。JetPack 7，GPU 在本機。」 | JetPack 7 |
| B02 | 0:05–0:10 | Dify 三欄 JSON | 「聖旨只有三欄。Dify 只准沾這一段。」 | Dify |
| B03 | 0:10–0:16 | Reachy＋波形＋頭轉向說話的人 | 「四麥聽方向，STT 進驛站，TTS 回宮門。」 | 4 Mic、DOA、STT／TTS |
| B04 | 0:16–0:21 | YOLO 框住荔枝盒與人 | 「TensorRT YOLO。認的是果，不是雲。」 | YOLO-TRT |
| B05 | 0:21–0:26 | K10 對人臉／對樹 | 「探子驗身。枝頭讀溫度、濕度、日照。」 | K10 臉、物候 |
| B06 | 0:26–0:32 | 物候三條數＋「已熟」 | 「氣候對，才放飛鴿。風大則駁回。」 | AHT20、光、加速度 |
| B07 | 0:32–0:39 | 兩座燈塔掃光＋xyz 軌跡＋落墊 | 「雙闕定位。飛鴿知枝頭在哪，毫米落地。」 | Lighthouse |
| B08 | 0:39–0:45 | MQTT、狗夾盒、MCP 清單 | 「牒走 MQTT。驛馬傳果。」 | MQTT、Dogzilla |
| B09 | 0:45–0:51 | K10 按 A，分屏「模型／準奏」 | 「語言模型可以擬旨，不能一人准奏。」 | 確認閘 |
| B10 | 0:51–0:55 | ComfyUI 出唐宮靜幀 | 「夢境也在同一塊 GPU 上。」 | ComfyUI |
| B11 | 0:55–1:00 | 黑，小字 | 「飛鴿探枝 · 驛馬送荔 · 決策不出宮」 | 收 |

旁白總字數壓在 90 字左右，不要念縮寫全稱兩遍。字幕可出現 `JetPack 7` `YOLO` `MQTT` `TTS/STT`。

---

## 四、K10「荔枝樹」怎麼架（花絮專用、正片可閃 1 秒）

1. 盆景或真枝當「嶺南」；K10 綁在枝側，鏡頭對準葉與果（或替代紅球）。  
2. 螢幕輪播：`26.4°C` `72%` `lux 8400` `枝頭已熟`。  
3. 用手遮光、呵氣增濕，錄一條數值變化——這就是「氣候環境變化」。  
4. 晃樹（加速度跳）→ 螢幕「風急，緩放飛」。對上飛鴿不盲飛。  
5. 可選：K10 人臉，驛卒（操作者）入鏡才允許按 A。

MQTT 示意 topic（花絮 UI 用，不必一次做完）：

```text
lychee/climate   {"t":26.4,"rh":72,"lux":8400,"ready":true}
lychee/pose      {"x":1.21,"y":0.44,"z":0.51,"fix":"lighthouse"}
lychee/scout     {"see":"lychee_box","where":"table_left"}
lychee/horse     {"phase":"grasp"}
lychee/gate      {"allow":true}
```

---

## 五、對長官／對課程各講 20 秒

**長官**  
第一趟驛馬很快，帶回的不是荔枝——沒有飛鴿、沒有火眼。第二趟掌事加持：燈塔飛鴿定位，狗到點用 YOLO 認荔才准夾。貴妃是收件人。驛站在 Thor。探子在樹下報氣候。按了 A 才準飛、準夾。夢境也是同一顆 GPU 補的。

**Dify 課**  
大腦不是 Dify。Dify 只出 JSON。含金量在 JetPack 7 上的感知鏈：STT → 規劃 → VLM／YOLO → MQTT → Lighthouse 飛鴿與驛馬，外加 K10 物候與人臉當現場條件。

**不要講**  
「我們用 AI 生成了整部宮廷劇。」真機 A  lev 在，AI 只補貴妃與唐朝夢。
