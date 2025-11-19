import json
from datetime import datetime
from shapely.geometry import Point
from shapely.ops import nearest_points
import cloudscraper
from sqlalchemy import func
import os
from config import TAIWAN_12NM_POLYGON, TAIWAN_24NM_POLYGON
from utils import safe_float, haversine, log_failed_record
from models import (
    db, ShipAIS,
    TestShipAIS, BoatShipAIS,
    BoatCheck12AIS, BoatCheck24AIS,
    CCGShipAIS, CCGCheck12ShipAIS, CCGCheck24ShipAIS,
    TestSession, BoatSession, BoatCheck12Session, BoatCheck24Session,
    CCGSession, CCGCheck12Session, CCGCheck24Session, ChinaBoatSession, ChinaBoatAIS
)

# 這裡就是你的 line_push.py 檔案
from line_push import send_line_alert, send_custom_zone_line_alert
from config import ENABLE_LINE_PUSH, ENABLE_EMAIL_ALERT, ALERT_EMAIL_TO
from mail_alert import send_alert_email, build_html_email



# === 自訂警戒區 ===
from shapely.geometry import shape
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ⭐ 全域變數（提供 API 用）
last_custom_zone_list = []

# 警戒區 DB 路徑
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ALARM_DB_PATH = os.path.join(ROOT_DIR, "db", "alarm_zones.db")

AlarmEngine = create_engine(
    f"sqlite:///{ALARM_DB_PATH}",
    connect_args={"check_same_thread": False}
)
AlarmSessionLocal = sessionmaker(bind=AlarmEngine)


# =========================================
# MarineTraffic API URL 列表
# =========================================
urls = [
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:426/Y:217/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:427/Y:217/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:426/Y:216/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:425/Y:217/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:426/Y:218/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:425/Y:216/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:427/Y:216/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:425/Y:218/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:427/Y:218/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:428/Y:216/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:428/Y:217/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:428/Y:218/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:429/Y:216/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:429/Y:217/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:429/Y:218/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:430/Y:216/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:430/Y:217/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:430/Y:218/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:213/Y:107/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:213/Y:108/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:213/Y:109/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:214/Y:107/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:214/Y:108/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:214/Y:109/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:215/Y:107/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:215/Y:108/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:215/Y:109/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:8/X:107/Y:53/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:8/X:107/Y:54/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:8/X:107/Y:55/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:8/X:108/Y:53/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:8/X:108/Y:54/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:8/X:108/Y:55/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:215/Y:108/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:215/Y:109/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:216/Y:108/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:216/Y:109/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:423/Y:219/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:423/Y:220/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:423/Y:221/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:424/Y:219/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:424/Y:220/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:424/Y:221/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:425/Y:219/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:425/Y:220/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:10/X:425/Y:221/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:11/X:848/Y:439/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:11/X:848/Y:440/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:11/X:848/Y:441/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:11/X:849/Y:439/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:11/X:849/Y:440/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:11/X:849/Y:441/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:211/Y:109/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:211/Y:110/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:212/Y:108/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:212/Y:109/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:212/Y:110/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:213/Y:108/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:213/Y:109/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:213/Y:110/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:214/Y:108/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:214/Y:109/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:211/Y:110/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:211/Y:111/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:212/Y:109/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:212/Y:110/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:212/Y:111/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:213/Y:108/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:213/Y:109/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:213/Y:110/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:213/Y:111/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:214/Y:108/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:214/Y:109/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:214/Y:110/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:215/Y:108/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:215/Y:109/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:216/Y:108/station:0",
    "https://www.marinetraffic.com/getData/get_data_json_4/z:9/X:216/Y:109/station:0"
]


# 建立爬蟲 client
scraper = cloudscraper.create_scraper()


# =========================================
# 共用函式：有就更新，沒有就新增
# =========================================
def upsert_ship(session, Model, ship_id, values_dict):
    record = session.query(Model).filter_by(ship_id=ship_id).first()
    if record:
        for key, val in values_dict.items():
            setattr(record, key, val)
    else:
        session.add(Model(**values_dict))


def load_custom_alarm_zones():
    """載入自訂警戒區，轉成 Shapely Polygon"""
    session = AlarmSessionLocal()
    rows = session.execute(
        text("SELECT id, name, geojson FROM alarm_zones")
    ).fetchall()
    session.close()

    zones = []
    for row in rows:
        geom = json.loads(row[2])
        zones.append({
            "id": row[0],
            "name": row[1],
            "polygon": shape(geom)
        })

    return zones


# =========================================
# 主函式：抓取 + 儲存 + 分類
# =========================================


def fetch_data(force_push=False):
    timestamp = datetime.utcnow()
    print(f"[{timestamp}] 🚢 Fetching AIS data...")

    seen_ships = set()
    # 讀取自訂警戒區
    custom_zones = load_custom_alarm_zones()
    CN_custom_zone_list = []   # ⭐ 存 CN 船在自訂警戒區裡的結果


    # *** 新增 ***
    # 建立兩個列表，用來收集要推播的船隻
    ships_inside_list = []
    ships_outside_list = []
    # ************

    # === 每次重抓前，清空 data_test.db ===
    try:
        TestSession.query(TestShipAIS).delete()
        TestSession.commit()
        print("🧹 Cleared data_test.db")
    except Exception as e:
        TestSession.rollback()
        log_failed_record({}, f"Clear data_test failed: {e}")

    scraper = cloudscraper.create_scraper()

    for url in urls:
        try:
            response = scraper.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            log_failed_record({"url": url}, f"Fetch error: {e}")
            continue

        key = url.replace("https://www.marinetraffic.com/getData/",
                          "").replace("/", "_").replace(":", "_")
        rows = data.get("data", {}).get("rows", [])
        if not rows:
            continue

        for row in rows:

            # === ⭐ 避免同一艘船在多個 tile 重複觸發 ===
            ship_id = row.get("SHIP_ID")
            if ship_id in seen_ships:
                continue
            seen_ships.add(ship_id)
            # ===============================================

            lat = safe_float(row.get("LAT"))
            lon = safe_float(row.get("LON"))
            shipname = row.get("SHIPNAME") or ""
            ship_id = row.get("SHIP_ID")


            if not (lat and lon and ship_id):
                continue

            record_kwargs = {
                "timestamp": timestamp,  # 這裡的 timestamp 是 datetime 物件
                "source": key,
                "ship_id": ship_id,
                "shipname": shipname,
                "lat": lat,
                "lon": lon,
                "speed": safe_float(row.get("SPEED")) / 10,
                "course": safe_float(row.get("COURSE")),
                "heading": safe_float(row.get("HEADING")),
                "rot": safe_float(row.get("ROT")),
                "destination": row.get("DESTINATION"),
                "dwt": row.get("DWT"),
                "flag": row.get("FLAG"),
                "shiptype": row.get("SHIPTYPE"),
                "gt_shiptype": row.get("GT_SHIPTYPE"),
                "length": row.get("LENGTH"),
                "width": row.get("WIDTH"),
            }

            # === 所有船隻歷史資料 ===
            db.session.add(ShipAIS(**record_kwargs))
            # === 最新資料（覆蓋寫入）===
            upsert_ship(TestSession, TestShipAIS, ship_id, record_kwargs)

            # === 若為中國籍船舶 (flag == "CN") ===
            if record_kwargs.get("flag") == "CN":
                ChinaBoatSession.add(ChinaBoatAIS(**record_kwargs))
                # === 自訂警戒區判斷 ===
                p = Point(lon, lat)

                for zone in custom_zones:
                    if p.within(zone["polygon"]):
                        CN_custom_zone_list.append({
                            "zone_id": zone["id"],
                            "zone_name": zone["name"],
                            "shipname": shipname,
                            "lat": lat,
                            "lon": lon,
                            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S")
                        })

            # === 若為海警船 ===
            if shipname.startswith("CHINACOASTGUARD"):
                BoatSession.add(BoatShipAIS(**record_kwargs))
                upsert_ship(CCGSession, CCGShipAIS, ship_id, record_kwargs)

                p = Point(lon, lat)
                in_12nm = p.within(TAIWAN_12NM_POLYGON)
                in_24nm = p.within(TAIWAN_24NM_POLYGON)

                # *** 修改：將 timestamp 轉為字串 ***
                # line_push 函式需要的是字串
                time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

                # ✅ 12nm 內
                if in_12nm:
                    BoatCheck12Session.add(BoatCheck12AIS(**record_kwargs))
                    upsert_ship(CCGCheck12Session, CCGCheck12ShipAIS,
                                ship_id, record_kwargs)
                    print(f"🚨 {shipname} 進入 12nm")

                    # *** 新增 ***
                    # 加入到 12 海浬推播列表
                    ships_inside_list.append({
                        'shipname': shipname,
                        'lat': lat,
                        'lon': lon,
                        'course': record_kwargs['course'],
                        'speed': record_kwargs['speed'],
                        'timestamp': time_str
                    })

                # ✅ 12–24nm 間（在 24nm 內但不在 12nm 內）
                elif in_24nm and not in_12nm:
                    BoatCheck24Session.add(BoatCheck24AIS(**record_kwargs))
                    upsert_ship(CCGCheck24Session, CCGCheck24ShipAIS,
                                ship_id, record_kwargs)
                    print(f"⚠️ {shipname} 在 12–24nm 之間")

                    # *** 新增 ***
                    # 計算到 12nm 邊界的距離 (line_push 函式需要這個)
                    p_12nm, _ = nearest_points(TAIWAN_12NM_POLYGON, p)
                    distance_km = haversine(p.y, p.x, p_12nm.y, p_12nm.x)

                    # 加入到 12-24 海浬推播列表
                    ships_outside_list.append({
                        'shipname': shipname,
                        'lat': lat,
                        'lon': lon,
                        'course': record_kwargs['course'],
                        'speed': record_kwargs['speed'],
                        'timestamp': time_str,
                        'distance_km': distance_km  # 推播函式需要的額外欄位
                    })


    # === *** 新增：觸發推播（全部 URL 抓完後才執行一次） *** ===
    print(f"📊 抓取完成. 12nm 內: {len(ships_inside_list)} 艘, 12-24nm: {len(ships_outside_list)} 艘")
    # === 自訂警戒區結果去重複 (依 shipname + zone_id) ===
    unique_cn_zones = {}
    for s in CN_custom_zone_list:
        key = (s["shipname"], s["zone_id"])  # 每艘船 + 區域，只留一筆
        unique_cn_zones[key] = s

    CN_custom_zone_list = list(unique_cn_zones.values())



    if ships_inside_list or ships_outside_list or force_push:

        # --- LINE 推播 ---
        if ENABLE_LINE_PUSH:
            print("🚀 正在觸發 LINE 推播...")
            try:
                send_line_alert(
                    ships_inside_list,
                    ships_outside_list,
                    force=force_push,
                    send_empty_summary=force_push
                )
            except Exception as e:
                print(f"❌ LINE 推播失敗: {e}")
        else:
            print("⚠️ LINE 推播已停用，跳過推播")


        # --- Gmail 推播（合併送出一封） ---
        if ENABLE_EMAIL_ALERT and ALERT_EMAIL_TO:
            print("📨 正在觸發 Gmail 警報...")

            try:
                # 判斷標題
                if ships_inside_list:
                    subject = "🚨 中國海警船闖入 12 海浬 + 自訂警戒區動態"
                elif ships_outside_list:
                    subject = "⚠️ 中國海警船進入 12-24 海浬 + 自訂警戒區動態"
                elif CN_custom_zone_list:
                    subject = "🚧 CN 船舶進入自訂警戒區"
                else:
                    subject = "📩 系統啟動報平安"

                # 建立 Email HTML 內容
                html = f"<h2>{subject}</h2>"

                # 12nm 內
                if ships_inside_list:
                    html += "<h3>🚨 12 海浬內船舶</h3>"
                    for s in ships_inside_list:
                        html += f"""
                        <div>
                            <b>{s['shipname']}</b><br>
                            📍 {s['lat']}, {s['lon']}<br>

                            🌐 <a href="https://www.google.com/maps?q={s['lat']},{s['lon']}">Google Maps</a><br>
                            🚢 <a href="https://www.marinetraffic.com/en/ais/home/centerx:{s['lon']}/centery:{s['lat']}/zoom:12">
                                MarineTraffic
                            </a><br>

                            <hr>
                        </div>
                        """


                # 12–24nm
                if ships_outside_list:
                    html += "<h3>⚠️ 12–24 海浬船舶</h3>"
                    for s in ships_outside_list:
                        html += f"""
                        <div>
                            <b>{s['shipname']}</b><br>
                            📍 {s['lat']}, {s['lon']}<br>
                            📏 距 12nm 約 {s.get('distance_km', 0):.2f} km<br>

                            🌐 <a href="https://www.google.com/maps?q={s['lat']},{s['lon']}">Google Maps</a><br>
                            🚢 <a href="https://www.marinetraffic.com/en/ais/home/centerx:{s['lon']}/centery:{s['lat']}/zoom:12">
                                MarineTraffic
                            </a><br>

                            <hr>
                        </div>
                        """

                # 🚧 自訂警戒區 — 按區域分組後輸出
                if CN_custom_zone_list:
                    html += "<h3>🚧 CN 船舶進入自訂警戒區</h3>"

                    # 先按 zone_name 分組
                    zone_groups = {}
                    for s in CN_custom_zone_list:
                        zone = s["zone_name"]
                        if zone not in zone_groups:
                            zone_groups[zone] = []
                        zone_groups[zone].append(s)

                    # 輸出格式：
                    # 【區域名稱】
                    #   • 船名（含座標 + 連結）
                    for zone_name, ships in zone_groups.items():
                        html += f"<h4>【{zone_name}】</h4>"

                        for s in ships:
                            html += f"""
                            <div style="margin-left:20px;">
                                • <b>{s['shipname']}</b><br>
                                📍 {s['lat']}, {s['lon']}<br>
                                🌐 <a href="https://www.google.com/maps?q={s['lat']},{s['lon']}">Google Maps</a><br>
                                🚢 <a href="https://www.marinetraffic.com/en/ais/home/centerx:{s['lon']}/centery:{s['lat']}/zoom:12">MarineTraffic</a><br>
                                <br>
                            </div>
                            """



                # 寄出
                send_alert_email(subject, html, ALERT_EMAIL_TO)

            except Exception as e:
                print(f"❌ Gmail 推播失敗: {e}")



    else:
        print("ℹ️ 無海警船可通報，且非 force_push，本次跳過推播。")


    # === *** 推播區塊結束 *** ===

    # === 提交各 DB ===
    try:
        db.session.commit()
        TestSession.commit()
        BoatSession.commit()
        BoatCheck12Session.commit()
        BoatCheck24Session.commit()
        CCGSession.commit()
        CCGCheck12Session.commit()
        CCGCheck24Session.commit()
        ChinaBoatSession.commit()

    except Exception as e:
        db.session.rollback()
        TestSession.rollback()
        BoatSession.rollback()
        BoatCheck12Session.rollback()
        BoatCheck24Session.rollback()
        CCGSession.rollback()
        CCGCheck12Session.rollback()
        CCGCheck24Session.rollback()
        ChinaBoatSession.rollback()
        log_failed_record({"url": "N/A - DB Commit"}, f"DB commit error: {e}")


