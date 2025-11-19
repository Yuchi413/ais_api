import os
import json
from dotenv import load_dotenv, find_dotenv
from shapely.geometry import Polygon

# =========================================
# 載入 .env
# =========================================
load_dotenv(find_dotenv())

# =========================================
# LINE 設定（可被 ENABLE_LINE_PUSH 控制）
# =========================================
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_TARGET_USER_ID = os.getenv("LINE_TARGET_USER_ID", "")

ENABLE_LINE_PUSH = os.getenv("ENABLE_LINE_PUSH", "False").lower() == "true"

# =========================================
# Gmail 設定（可被 ENABLE_EMAIL_ALERT 控制）
# =========================================
GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_PASS = os.getenv("GMAIL_PASS", "")

ENABLE_EMAIL_ALERT = os.getenv("ENABLE_EMAIL_ALERT", "False").lower() == "true"
ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO", "")

# =========================================
# DB 設定
# =========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "db")
os.makedirs(DB_DIR, exist_ok=True)

MAIN_DB_PATH = os.path.join(DB_DIR, "ais_data.db")
TEST_DB_PATH = os.path.join(DB_DIR, "data_test.db")
BOAT_DB_PATH = os.path.join(DB_DIR, "boat_test.db")
BOAT_CHECK12_DB_PATH = os.path.join(DB_DIR, "boat_check12.db")
BOAT_CHECK24_DB_PATH = os.path.join(DB_DIR, "boat_check24.db")
CCG_DB_PATH = os.path.join(DB_DIR, "ccg.db")
CCG_CHECK12_DB_PATH = os.path.join(DB_DIR, "ccg_check12.db")
CCG_CHECK24_DB_PATH = os.path.join(DB_DIR, "ccg_check24.db")
CHINA_BOAT_DB_PATH = os.path.join(DB_DIR, "chinaboat.db")

FAILED_LOG_FILE = os.path.join(BASE_DIR, "failed_records.json")

# =========================================
# GeoJSON 載入
# =========================================
def load_geojson_polygon(filename):
    path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(path):
        print(f"[config] ⚠️ 找不到 {filename}")
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        coords = []

        for feature in data.get("features", []):
            geom = feature.get("geometry", {})
            geom_type = geom.get("type")
            geom_coords = geom.get("coordinates", [])

            if geom_type == "Polygon":
                coords.extend(geom_coords[0])
            elif geom_type == "MultiPolygon":
                for poly in geom_coords:
                    coords.extend(poly[0])
            elif geom_type in ["LineString", "MultiLineString"]:
                line_coords = (
                    geom_coords if geom_type == "LineString"
                    else [pt for line in geom_coords for pt in line]
                )
                if line_coords[0] != line_coords[-1]:
                    line_coords.append(line_coords[0])
                coords.extend(line_coords)

        poly = Polygon(coords).buffer(0)
        print(f"[config] ✅ 載入 {filename} 成功，共 {len(coords)} 點")
        return poly

    except Exception as e:
        print(f"[config] ⚠️ 載入 {filename} 失敗: {e}")
        return None

TAIWAN_12NM_POLYGON = load_geojson_polygon("static/taiwan_12nm.geojson")
TAIWAN_24NM_POLYGON = load_geojson_polygon("static/taiwan_24nm.geojson")

TAIWAN_POLYGON = TAIWAN_12NM_POLYGON
