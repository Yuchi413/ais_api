# 🛰️ AI 智能海域監控與預警系統  
**AI-Driven Maritime Intelligence & Defense Platform**

本系統整合 AIS 船舶資料、地理空間分析、航行警告解析，以及 AI 語意處理技術，旨在打造一套具備 **即時監控、風險判讀與自動警報** 的海域安全預警平台。  
適用於國防情資應用、海域安全監測、學術研究與示範展示。

---

## 📌 系統功能特色

### 1️⃣ **AIS 船舶即時監控**
- 從 MarineTraffic 資料來源擷取船隻資訊  
- 自動分類：
  - 中國海警（CHINACOASTGUARD）
  - 中國籍船舶（CN Flag）
  - 特定黑名單船舶  
- 打包成統一格式供前端展示（GeoJSON / JSON）

---

### 2️⃣ **12 海里 & 24 海里警戒區自動判斷**
- 載入 taiwan_12nm.geojson & taiwan_24nm.geojson  
- 判斷船隻是否進入：
  - 12 nm 領海警戒區
  - 24 nm 緩衝區  
- 自動計算距離最近的地點（使用 Shapely）

---

### 3️⃣ **自動推播 LINE 警報**
若船隻進入警戒區，系統會自動推送：

- 船名、MMSI、國籍  
- 經緯度 + Map URL  
- 距離最近陸地點  
- 所屬緯度格  

並內建重複警報防護（Hash + Cooldown）。

---

### 4️⃣ **航行警告（航警）自動解析**
- 自動抓取中國海事局航警資料  
- AI 解析文字中的經緯度、射擊區範圍  
- 繪製成 GeoJSON  
- 可與 AIS 數據疊合顯示

---

### 5️⃣ **Web 前端 3D 顯示介面（CesiumJS）**
- 支援船隻位置顯示  
- 支援警戒區疊圖  
- 支援多圖層切換  
- 支援黑名單即時查詢  
- 支援自訂警戒區顯示  

---

## 🗂️ 專案結構（Project Structure）

```

SIMPLE_AIS_API/
│
├── app.py                 # Flask 主程式
├── fetcher.py             # AIS 下載 / 解析
├── scheduler.py           # APScheduler 排程
├── database.py            # SQLAlchemy 設定
├── models.py              # Database ORM Models
├── config.py              # 設定檔（非敏感）
├── utils.py               # 共用工具函式
│
├── routes/                # API 路由
│   ├── api.py
│   ├── web.py
│   ├── blacklist.py
│   └── alarm_api.py
│
├── static/                # 靜態前端資料
│   ├── ships_map.html
│   ├── taiwan_12nm.geojson
│   └── taiwan_24nm.geojson
│
├── templates/             # Flask HTML 模板
│   └── ship.html
│
├── alarm_loader.py        # 航警自動解析/載入
├── line_push.py           # LINE 推播服務
├── mail_alert.py          # Gmail Email 警報（選用）
│
├── requirements.txt       # Python 套件列表
├── .gitignore             # 避免 .env / .db 洩漏
└── README.md

````

---

## 🛠️ 安裝與啟動方式

### **1️⃣ 建立 Virtual Environment**
```bash
python -m venv env
source env/bin/activate   # Windows: env\Scripts\activate
````

### **2️⃣ 安裝需求套件**

```bash
pip install -r requirements.txt
```

### **3️⃣ 建立 `.env`（此檔案不會上傳 GitHub）**

內容範例：

```
# === LINE 設定 ===
LINE_ACCESS_TOKEN=
LINE_CHANNEL_SECRET=
LINE_TARGET_USER_ID=

# 是否啟用 LINE 推播
ENABLE_LINE_PUSH=False

# === Gmail 寄信設定 ===
GMAIL_USER=
GMAIL_PASS=
ALERT_EMAIL_TO=
#不想再被 email 轟炸，只要把 ENABLE_EMAIL_ALERT=false 就直接關掉。

# 是否啟用 Gmail 警報
ENABLE_EMAIL_ALERT=true
```

### **4️⃣ 啟動 Flask API**

```bash
python app.py
```

---

## 🛰️ API Endpoints

### 🚢 `/api/ships`

回傳所有監測到的 AIS 船舶資訊。

### ⚠ `/api/alerts`

檢查是否有船隻進入 12/24 海里。

### 🎯 `/api/blacklist`

查詢/更新黑名單。

### 🗺 `/`

前端 Cesium 3D 顯示介面。

---

## 🔐 安全設計

* `.env` 已加入 `.gitignore`，避免金鑰外洩
* `.db` 本地資料庫不會上傳
* API Key、Gmail、LINE Token 不存入 repo

---

## 📌 使用技術 Technology Stack

* **Python** — Flask / SQLAlchemy / APScheduler
* **GIS** — Shapely / GeoJSON / CesiumJS
* **AI** — OpenAI API（航警文字解析）
* **Data Source** — MarineTraffic AIS
* **Alerting** — LINE Messaging API / Gmail API

