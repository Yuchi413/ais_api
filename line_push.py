import os
import json
import hashlib
from datetime import datetime, timedelta

from linebot import LineBotApi, WebhookHandler
from linebot.models import FlexSendMessage

from config import (
    LINE_ACCESS_TOKEN, LINE_CHANNEL_SECRET, LINE_TARGET_USER_ID,
    ENABLE_LINE_PUSH
)
from utils import (
    describe_location_text,
    nearest_reference_point
)

# =========================================
# LINE API 初始化
# =========================================
line_bot_api = LineBotApi(LINE_ACCESS_TOKEN) if LINE_ACCESS_TOKEN else None
handler = WebhookHandler(LINE_CHANNEL_SECRET) if LINE_CHANNEL_SECRET else None

# =========================================
# 推播防重複機制
# =========================================
_last_push_hash_enter = None
_last_push_hash_exit = None
_last_push_time = None
PUSH_COOLDOWN = timedelta(minutes=8)

# =========================================
# 狀態儲存檔
# =========================================
STATE_FILE = "state_cache.json"


# =========================================
# 工具：安全推播（會檢查 ENABLE_LINE_PUSH）
# =========================================
def safe_push(user_id, message):
    if not ENABLE_LINE_PUSH:
        print("[LINE PUSH] 已停用，訊息不會發送")
        return
    if line_bot_api:
        line_bot_api.push_message(user_id, message)


# =========================================
# 狀態檔案
# =========================================
def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[STATE] write failed: {e}")


# =========================================
# 時間轉換：UTC → 台灣
# =========================================
def utc_to_taipei(ts):
    try:
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") + timedelta(hours=8)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return ts


# =========================================
# （原本功能）Flex 卡片：12nm / 12–24nm 警戒
# =========================================
def build_flex_card(ship):
    lat = float(ship["lat"])
    lon = float(ship["lon"])
    course = ship.get("course")
    speed = ship.get("speed")
    name = ship.get("shipname", "UNKNOWN")
    ts_local = utc_to_taipei(ship.get("timestamp", ""))
    zone = ship.get("zone", "unknown")

    if zone == "12":
        header_color = "#B71C1C"
        header_text = "🚨 中國海警船闖入台灣 12 海浬內！"
    elif zone == "12-24":
        header_color = "#EF6C00"
        header_text = "⚠️ 中國海警船進入 12–24 海浬"
    else:
        header_color = "#1565C0"
        header_text = "🌊 海域外船舶"

    location_text = describe_location_text(lat, lon)
    speed_text = f"{float(speed):.1f} 節" if speed is not None else "— 節"
    map_url = f"https://www.google.com/maps?q={lat},{lon}&z=8"

    return {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": header_color,
            "contents": [
                {"type": "text", "text": header_text, "weight": "bold", "color": "#FFFFFF", "wrap": True}
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {"type": "text", "text": f"🚢 {name}", "weight": "bold", "size": "md"},
                {"type": "text", "text": f"📍 {lat:.6f}, {lon:.6f}", "size": "sm"},
                {"type": "text", "text": f"➡️ 航向 {course}° | {speed_text}", "size": "sm"},
                {"type": "text", "text": f"🕒 資料時間 {ts_local}", "size": "sm"},
                {"type": "separator", "margin": "md"},
                {"type": "text", "text": f"📌 {location_text}", "size": "sm", "wrap": True}
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "color": header_color,
                    "action": {
                        "type": "uri",
                        "label": "🌍 Google Maps",
                        "uri": map_url
                    }
                },
                {
                    "type": "button",
                    "style": "link",
                    "action": {
                        "type": "uri",
                        "label": "📡 MarineTraffic",
                        "uri": f"https://www.marinetraffic.com/en/ais/home/centerx:{lon}/centery:{lat}/zoom:12"
                    }
                }
            ]
        }
    }


def build_flex_carousel(ships):
    bubbles = [build_flex_card(s) for s in ships]
    return FlexSendMessage(
        alt_text="中國海警船動態通知",
        contents={"type": "carousel", "contents": bubbles[:12]}
    )


# =========================================
# 離開警戒區通知
# =========================================
def build_departure_flex(exited_ships):
    now = datetime.utcnow() + timedelta(hours=8)
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    body_list = []
    for s in exited_ships:
        lat = float(s["lat"])
        lon = float(s["lon"])
        ref_name, dist_nm = nearest_reference_point(lat, lon)
        body_list.append({
            "type": "text",
            "text": f"🚢 {s['shipname']}　📏 距{ref_name} {dist_nm:.1f} 海浬",
            "size": "sm",
            "wrap": True
        })

    return FlexSendMessage(
        alt_text="中國海警船離開警戒區",
        contents={
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#2E7D32",
                "contents": [
                    {"type": "text", "text": "🟢【情資更新：已離開警戒】", "weight": "bold", "color": "#FFFFFF"}
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": "已退出以下海域：", "wrap": True, "size": "sm"},
                    *body_list,
                    {"type": "separator", "margin": "md"},
                    {"type": "text", "text": f"🕒 {now_str}", "size": "xs", "color": "#777777"}
                ]
            }
        }
    )


def detect_exited_ships(prev_state, current_ships):
    prev_names = set(prev_state.keys())
    current_names = set(s["shipname"] for s in current_ships)
    exited = prev_names - current_names
    return [prev_state[name] for name in exited]


# =========================================
# ⭐⭐【新增】自訂警戒區 Flex 卡片⭐⭐
# =========================================
def build_custom_zone_card(ship):
    google_url = f"https://www.google.com/maps?q={ship['lat']},{ship['lon']}"
    return {
        "type": "bubble",
        "size": "micro",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "paddingAll": "12px",
            "contents": [
                {"type": "text", "text": "🚧 自訂警戒區入侵", "weight": "bold", "size": "md", "color": "#D32F2F"},
                {"type": "text", "text": f"區域：{ship['zone_name']}", "wrap": True, "size": "sm"},
                {"type": "text", "text": f"船名：{ship['shipname']}", "wrap": True, "size": "sm"},
                {"type": "text", "text": f"座標：{ship['lat']:.4f},{ship['lon']:.4f}", "size": "xs"},
                {"type": "text", "text": f"時間：{ship['timestamp']}", "size": "xs", "color": "#777"},
                {
                    "type": "button",
                    "style": "link",
                    "height": "sm",
                    "action": {
                        "type": "uri",
                        "label": "🌍 Google Maps",
                        "uri": google_url
                    }
                },
                {
                    "type": "button",
                    "style": "link",
                    "height": "sm",
                    "action": {
                        "type": "uri",
                        "label": "📡 MarineTraffic",
                        "uri": f"https://www.marinetraffic.com/en/ais/home/centerx:{ship['lon']}/centery:{ship['lat']}/zoom:12"
                    }
                }
            ]
        }
    }


def send_custom_zone_line_alert(ship_list):
    """自訂警戒區推播"""
    if not ENABLE_LINE_PUSH:
        print("[CUSTOM ZONE] LINE 推播停用")
        return

    if not ship_list:
        print("[CUSTOM ZONE] 無資料可推播")
        return

    bubbles = [build_custom_zone_card(s) for s in ship_list][:10]

    msg = FlexSendMessage(
        alt_text="🚧 自訂警戒區入侵警報",
        contents={"type": "carousel", "contents": bubbles}
    )

    try:
        line_bot_api.push_message(LINE_TARGET_USER_ID, msg)
        print("📩 自訂警戒區 LINE 推播成功")
    except Exception as e:
        print("❌ 自訂警戒區 LINE 推播失敗：", e)


# =========================================
# 原本主推播函式（12nm / 12–24nm）
# =========================================
def send_line_alert(ships_inside, ships_outside, *, force=False, send_empty_summary=False):
    global _last_push_hash_enter, _last_push_hash_exit, _last_push_time

    if not ENABLE_LINE_PUSH:
        print("[LINE] 推播已停用")
        return

    if not line_bot_api or not LINE_TARGET_USER_ID:
        print("[LINE] 缺少憑證，無法推播")
        return

    for s in ships_inside:
        s["zone"] = "12"
    for s in ships_outside:
        s["zone"] = "12-24"

    entering = ships_inside + ships_outside

    prev_state = load_state()
    current_state = {s["shipname"]: s for s in entering}
    exited_ships = detect_exited_ships(prev_state, entering)

    # 進入警戒推播
    if entering:
        hash_enter = hashlib.sha256(json.dumps(entering, sort_keys=True).encode()).hexdigest()
        now = datetime.utcnow()

        if force or (_last_push_hash_enter != hash_enter or not _last_push_time or now - _last_push_time > PUSH_COOLDOWN):
            flex_msg = build_flex_carousel(entering)
            line_bot_api.push_message(LINE_TARGET_USER_ID, flex_msg)
            _last_push_hash_enter = hash_enter
            _last_push_time = now
            print("[LINE] 已推播 ENTER 警報")

    # 離開警戒推播
    if exited_ships:
        hash_exit = hashlib.sha256(json.dumps(exited_ships, sort_keys=True).encode()).hexdigest()

        if force or (_last_push_hash_exit != hash_exit):
            flex_msg = build_departure_flex(exited_ships)
            line_bot_api.push_message(LINE_TARGET_USER_ID, flex_msg)
            _last_push_hash_exit = hash_exit
            print("[LINE] 已推播 EXIT 警報")

    save_state(current_state)
