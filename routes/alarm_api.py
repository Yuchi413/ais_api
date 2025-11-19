import os
import json
from flask import Blueprint, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base

# Blueprint
alarm_api = Blueprint("alarm_api", __name__)

# ===============================
#   設定資料庫位置 simple_ais_api/db
# ===============================
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT_DIR, "db", "alarm_zones.db")

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

# ===============================
#   定義警戒區資料表
# ===============================
class AlarmZone(Base):
    __tablename__ = "alarm_zones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    geojson = Column(Text, nullable=False)   # 存 polygon geometry

Base.metadata.create_all(engine)


# ===============================
#   GET：取得所有警戒區（回傳 GeoJSON）
# ===============================
@alarm_api.route("/alarm_zones", methods=["GET"])
def get_alarm_zones():
    session = SessionLocal()
    rows = session.query(AlarmZone).all()
    session.close()

    features = []
    for row in rows:
        geo = json.loads(row.geojson)
        features.append({
            "type": "Feature",
            "properties": {
                "id": row.id,
                "name": row.name
            },
            "geometry": geo
        })

    return jsonify({
        "type": "FeatureCollection",
        "features": features
    })


# ===============================
#   POST：儲存多個警戒區
# ===============================
@alarm_api.route("/alarm_zones", methods=["POST"])
def save_alarm_zones():
    data = request.get_json() or {}
    features = data.get("features", [])

    if not features:
        return jsonify({"error": "no features"}), 400

    session = SessionLocal()

    for f in features:
        name = f["properties"].get("name", "未命名警戒區")
        geometry = f["geometry"]

        zone = AlarmZone(
            name=name,
            geojson=json.dumps(geometry)
        )
        session.add(zone)

    session.commit()
    session.close()

    return jsonify({"status": "saved"}), 200


# ===============================
#   DELETE：刪除一個警戒區
# ===============================
@alarm_api.route("/alarm_zones/<int:zone_id>", methods=["DELETE"])
def delete_alarm_zone(zone_id):
    session = SessionLocal()
    row = session.query(AlarmZone).filter_by(id=zone_id).first()

    if not row:
        session.close()
        return jsonify({"error": "not found"}), 404

    session.delete(row)
    session.commit()
    session.close()

    return jsonify({"status": "deleted", "id": zone_id})
