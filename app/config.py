"""Contoso Inventory - 설정 파일 (온프렘 VM 버전)

온프렘 VM에서는 서버마다 이 파일을 직접 수정해서 배포했습니다.
값이 코드에 하드코딩되어 있어 환경(개발/운영)이 바뀔 때마다 코드를 고쳐야 합니다.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# VM의 로컬 디스크에 있는 SQLite 파일
DATABASE_URL = "sqlite:///" + os.path.join(BASE_DIR, "data", "inventory.db")

# VM의 로컬 디스크에 쌓이는 로그 파일
LOG_FILE = os.path.join(BASE_DIR, "logs", "app.log")

# 화면 하단/배너에 표시되는 버전 정보
APP_VERSION = "1.0"
BANNER_COLOR = "#0f6cbd"

PORT = 8080
