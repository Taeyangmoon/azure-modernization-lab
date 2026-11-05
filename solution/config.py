"""Contoso Inventory - 설정 파일 (컨테이너 / Azure Container Apps 버전)

모든 환경 설정을 환경 변수로 받습니다 (Twelve-Factor App: III. Config).
같은 컨테이너 이미지를 개발/운영에 그대로 쓰고, 값만 바꿔서 배포합니다.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# DATABASE_URL 이 없으면 로컬 SQLite 파일로 동작 (로컬 개발용)
# 예) postgresql+psycopg2://user:password@host:5432/inventory
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "data", "inventory.db")
)

# 화면 하단/배너에 표시되는 버전 정보
APP_VERSION = os.environ.get("APP_VERSION", "1.0")
BANNER_COLOR = os.environ.get("BANNER_COLOR", "#0f6cbd")

PORT = int(os.environ.get("PORT", "8080"))
