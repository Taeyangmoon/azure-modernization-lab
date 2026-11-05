"""Contoso Inventory - 재고 관리 웹 앱 (온프렘 VM 버전)

Flask + SQLAlchemy 로 만든 간단한 사내 재고 관리 앱입니다.
"""
import logging
import os
import socket
import sys
import time
from datetime import datetime

from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

import config

# ---------------------------------------------------------------------------
# 로깅: 파일이 아니라 stdout 으로 출력 (Container Apps 가 수집해서 Log Analytics 로 전송)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("inventory")

# ---------------------------------------------------------------------------
# 앱 / DB 초기화
# ---------------------------------------------------------------------------
os.makedirs(os.path.join(config.BASE_DIR, "data"), exist_ok=True)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = config.DATABASE_URL
db = SQLAlchemy(app)

STARTED_AT = time.time()


class Item(db.Model):
    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    location = db.Column(db.String(100), nullable=False, default="")
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "quantity": self.quantity,
            "location": self.location,
            "updated_at": self.updated_at.isoformat(),
        }


SAMPLE_ITEMS = [
    ("27인치 모니터", 14, "서울 본사 A-01"),
    ("무선 키보드", 40, "서울 본사 A-02"),
    ("무선 마우스", 38, "서울 본사 A-02"),
    ("USB-C 도킹 스테이션", 12, "서울 본사 B-03"),
    ("노트북 15인치", 9, "서울 본사 B-04"),
    ("웹캠 FHD", 25, "부산 지사 C-01"),
    ("헤드셋", 31, "부산 지사 C-02"),
    ("HDMI 케이블 2m", 120, "부산 지사 C-03"),
    ("랙 서버 1U", 3, "데이터센터 R-01"),
    ("UPS 1500VA", 6, "데이터센터 R-02"),
    ("10GbE 스위치 24포트", 2, "데이터센터 R-03"),
    ("라벨 프린터", 4, "서울 본사 D-01"),
]


def init_db():
    """테이블을 만들고, 비어 있으면 샘플 데이터를 넣습니다."""
    with app.app_context():
        try:
            db.create_all()
            if Item.query.count() == 0:
                for name, qty, loc in SAMPLE_ITEMS:
                    db.session.add(Item(name=name, quantity=qty, location=loc))
                db.session.commit()
                logger.info("Seeded %d sample items", len(SAMPLE_ITEMS))
        except SQLAlchemyError:
            db.session.rollback()
            logger.exception("DB 초기화 중 오류 (다른 프로세스가 먼저 초기화했을 수 있음)")


init_db()


# ---------------------------------------------------------------------------
# 라우트
# ---------------------------------------------------------------------------
def runtime_info():
    return {
        "hostname": socket.gethostname(),
        "version": config.APP_VERSION,
        "db_backend": db.engine.dialect.name,
        "uptime_seconds": int(time.time() - STARTED_AT),
    }


@app.route("/")
def index():
    items = Item.query.order_by(Item.id.desc()).all()
    return render_template(
        "index.html", items=items, info=runtime_info(), banner_color=config.BANNER_COLOR
    )


@app.route("/items", methods=["POST"])
def add_item():
    name = request.form.get("name", "").strip()
    location = request.form.get("location", "").strip()
    try:
        quantity = int(request.form.get("quantity", "0"))
    except ValueError:
        quantity = 0
    if name:
        db.session.add(Item(name=name, quantity=quantity, location=location))
        db.session.commit()
        logger.info("Item added: %s (qty=%s)", name, quantity)
    return redirect(url_for("index"))


@app.route("/items/<int:item_id>/delete", methods=["POST"])
def delete_item(item_id):
    item = db.session.get(Item, item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
        logger.info("Item deleted: id=%s", item_id)
    return redirect(url_for("index"))


@app.route("/api/items")
def api_items():
    return jsonify([i.to_dict() for i in Item.query.order_by(Item.id).all()])


@app.route("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify(status="ok", **runtime_info())
    except SQLAlchemyError:
        logger.exception("Health check failed")
        return jsonify(status="error", **runtime_info()), 503


if __name__ == "__main__":
    # 로컬 개발용 실행. 컨테이너에서는 gunicorn 이 app:app 을 실행합니다 (Dockerfile 참고).
    app.run(host="0.0.0.0", port=config.PORT)
