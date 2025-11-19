import os
from flask import Blueprint, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

# Blueprint
blacklist_api = Blueprint("blacklist_api", __name__)

# -------------------------------------
#  設定資料庫位置 simple_ais_api/db/
# -------------------------------------
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT_DIR, "db", "blacklist.db")

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

# -------------------------------------
#  定義黑名單 Table
# -------------------------------------
class Blacklist(Base):
    __tablename__ = "blacklist"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    note = Column(String, nullable=True)

Base.metadata.create_all(engine)


# -------------------------------------
#  GET：取得黑名單
# -------------------------------------
@blacklist_api.route("/blacklist_ships", methods=["GET"])
def list_blacklist():
    session = SessionLocal()
    rows = session.query(Blacklist).all()
    session.close()

    items = [{"id": r.id, "name": r.name, "note": r.note} for r in rows]
    return jsonify({"items": items})


# -------------------------------------
#  POST：新增黑名單
# -------------------------------------
@blacklist_api.route("/blacklist_ships", methods=["POST"])
def add_blacklist():
    data = request.json or {}
    name = (data.get("name") or "").strip()
    note = (data.get("note") or "").strip()

    if not name:
        return jsonify({"error": "name required"}), 400

    session = SessionLocal()
    row = Blacklist(name=name, note=note)
    session.add(row)
    session.commit()
    session.refresh(row)
    session.close()

    return jsonify({"id": row.id, "name": row.name, "note": row.note})


# -------------------------------------
#  DELETE：刪除黑名單
# -------------------------------------
@blacklist_api.route("/blacklist_ships/<int:item_id>", methods=["DELETE"])
def delete_blacklist(item_id):
    session = SessionLocal()
    row = session.query(Blacklist).filter_by(id=item_id).first()

    if not row:
        session.close()
        return jsonify({"error": "not found"}), 404

    session.delete(row)
    session.commit()
    session.close()

    return jsonify({"status": "ok", "id": item_id})
