# UNIHIKER K10 — 隨身助理：顯示取物任務 + A/B 確認閘
# 語音請走 Thor ASR 後 POST /voice；這支負責看 pending、按 A 讓機器狗出發。

from unihiker_k10 import button, rgb, screen
import time
import urequests

THOR = "http://192.168.8.195:8766"


def paint(lines, color=0xFFFFFF):
    screen.show_bg(color=0x102040)
    for idx, line in enumerate(lines[:8]):
        screen.draw_text(text=str(line)[:28], line=idx, font_size=16, color=color)
    screen.show_draw()


def get_json(path):
    res = urequests.get(THOR + path)
    try:
        return res.json()
    finally:
        res.close()


def post_json(path, payload):
    res = urequests.post(THOR + path, json=payload)
    try:
        return res.json()
    finally:
        res.close()


def show_idle():
    rgb.clear()
    paint(["K10 隨身助理", "等取物確認", "A 核准  B 拒絕", THOR.replace("http://", "")], 0x88CCFF)


def show_pending(item):
    dispatch = item.get("dispatch") or {}
    rgb.write(num=0, R=255, G=160, B=0)
    rgb.write(num=1, R=255, G=160, B=0)
    paint(
        [
            "機器狗取物",
            "拿 " + dispatch.get("item", "?"),
            "到 " + dispatch.get("dest", "?"),
            "給 " + dispatch.get("recipient", "?"),
            "A 出發",
            "B 取消",
        ],
        0xFFFF66,
    )


def resolve(pending_id, allow):
    body = post_json("/confirm", {"id": pending_id, "allow": allow})
    ok = body.get("status") == "ready"
    rgb.write(num=0, R=0 if not ok else 0, G=200 if ok else 0, B=0 if ok else 200)
    rgb.write(num=1, R=200 if not ok else 0, G=0 if not ok else 200, B=0)
    paint(["結果", body.get("status", "?"), (body.get("dispatch") or {}).get("say", "")], 0xAAFFAA if ok else 0xFF8888)
    time.sleep(1.5)


screen.init(dir=2)
btn_a = button(button.a)
btn_b = button(button.b)
show_idle()
last_id = ""

while True:
    try:
        state = get_json("/pending")
        pending = state.get("pending")
        if state.get("status") == "awaiting_confirm" and pending:
            if pending.get("id") != last_id:
                last_id = pending["id"]
                show_pending(pending)
            if btn_a.status() == 1:
                resolve(pending["id"], True)
                last_id = ""
                show_idle()
            elif btn_b.status() == 1:
                resolve(pending["id"], False)
                last_id = ""
                show_idle()
        else:
            if last_id:
                last_id = ""
                show_idle()
    except Exception as exc:
        paint(["連線失敗", str(exc)[:40], THOR], 0xFF6666)
    time.sleep(0.3)
