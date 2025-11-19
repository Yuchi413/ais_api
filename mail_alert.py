# mail_alert.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import GMAIL_USER, GMAIL_PASS


# --------------------------------------------------------
# 1) HTML 卡片生成（海巡署風格）
# --------------------------------------------------------
def build_html_email(title, ships):
    """產生海巡署風格 HTML 警戒信"""

    cards_html = ""
    for s in ships:
        lat = float(s["lat"])
        lon = float(s["lon"])
        name = s["shipname"]
        course = s.get("course", "—")
        speed = s.get("speed", "—")
        timestamp = s.get("timestamp", "")

        map_url = f"https://www.google.com/maps?q={lat},{lon}&z=10"
        ais_url = f"https://www.marinetraffic.com/en/ais/home/centerx:{lon}/centery:{lat}/zoom:12"

        cards_html += f"""
        <div style="
            border:1px solid #1E88E5;
            border-radius:8px;
            padding:12px;
            margin-bottom:12px;
            background:#F5FBFF;">
            
            <h3 style="margin:0; color:#0D47A1;">
                🚢 {name}
            </h3>

            <p style="margin:4px 0; font-size:14px;">
                📍 座標：<b>{lat:.5f}, {lon:.5f}</b><br>
                ➡️ 航向：<b>{course}°</b>　|　速度：<b>{speed} 節</b><br>
                🕒 時間：{timestamp}
            </p>

            <a href="{map_url}" style="
                display:inline-block;
                margin-top:6px;
                background:#1976D2;
                color:white;
                padding:8px 14px;
                border-radius:6px;
                text-decoration:none;
                font-size:14px;">
                🌍 查看地圖
            </a>

            <a href="{ais_url}" style="
                display:inline-block;
                margin-top:6px;
                margin-left:6px;
                background:#0D47A1;
                color:white;
                padding:8px 14px;
                border-radius:6px;
                text-decoration:none;
                font-size:14px;">
                📡 MarineTraffic 即時動態
            </a>
        </div>
        """

    html = f"""
    <html>
    <body style="font-family:Arial, sans-serif; background:#f2f6f9; padding:20px;">
        <div style="
            max-width:600px;
            margin:auto;
            background:white;
            border-radius:10px;
            padding:20px;
            border-top:6px solid #0D47A1;
            box-shadow:0 3px 8px rgba(0,0,0,0.1);
        ">

            <h2 style="margin-top:0; color:#0D47A1;">{title}</h2>

            {cards_html}

            <p style="font-size:12px; color:#666; margin-top:20px;">
                本通知由「智能海域監控與預警系統」自動發送。
            </p>
        </div>
    </body>
    </html>
    """

    return html


# --------------------------------------------------------
# 2) 寄送 HTML Email
# --------------------------------------------------------
def send_alert_email(subject: str, html_body: str, to_email: str):
    """寄送 HTML 格式警戒信"""

    if not GMAIL_USER or not GMAIL_PASS:
        print("⚠️ GMAIL_USER 或 GMAIL_PASS 未設定，略過寄信")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = GMAIL_USER
        msg["To"] = to_email

        # HTML 內容
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASS)
            server.sendmail(GMAIL_USER, [to_email], msg.as_string())

        print(f"📧 HTML 警戒信寄出成功 → {to_email}")

    except Exception as e:
        print(f"❌ 寄信失敗: {e}")
