# Lab 2. 코드 수정 + Dockerfile 작성 (30분)

## 목표
- 앱을 **최소한으로 수정**해 클라우드 네이티브 원칙(설정=환경변수, 로그=stdout)을 따르게 한다.
- 운영용 웹 서버(gunicorn)와 **Dockerfile** 을 추가한다.
- (선택) 로컬에서 컨테이너를 실행해 본다.

> 막히거나 시간이 부족하면 `solution/` 폴더의 파일을 `app/` 으로 복사해도 됩니다.
> 예) `cp solution/config.py app/config.py`

모든 작업은 `app/` 폴더에서 합니다.

## 2-1. 설정을 환경 변수로 (`app/config.py`)

`app/config.py` 전체를 아래 내용으로 **교체**합니다.

```python
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# DATABASE_URL 이 없으면 로컬 SQLite 파일로 동작 (로컬 개발용)
# 예) postgresql+psycopg2://user:password@host:5432/inventory
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "data", "inventory.db")
)

# 화면에 표시되는 버전/배너 색
APP_VERSION = os.environ.get("APP_VERSION", "1.0")
BANNER_COLOR = os.environ.get("BANNER_COLOR", "#0f6cbd")

PORT = int(os.environ.get("PORT", "8080"))
```

**변한 점**: `LOG_FILE` 설정이 사라지고, 나머지 값은 `os.environ.get(이름, 기본값)` 으로 읽습니다. 기본값이 있어서 로컬에서는 이전처럼 동작합니다.

## 2-2. 로그를 stdout 으로 (`app/app.py`)

`app.py` 상단 import 부분과 로깅 설정을 수정합니다.

**(1) import 수정** — `RotatingFileHandler` 줄을 지우고 `sys` 를 추가합니다.

```diff
 import logging
 import os
 import socket
+import sys
 import time
 from datetime import datetime
-from logging.handlers import RotatingFileHandler
```

**(2) 로깅 설정 수정**

```diff
 # ---------------------------------------------------------------------------
-# 로깅: VM 로컬 디스크의 파일에 기록
+# 로깅: 파일이 아니라 stdout 으로 출력 (Container Apps 가 수집해서 Log Analytics 로 전송)
 # ---------------------------------------------------------------------------
-os.makedirs(os.path.dirname(config.LOG_FILE), exist_ok=True)
-file_handler = RotatingFileHandler(config.LOG_FILE, maxBytes=1_000_000, backupCount=3)
-file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
-logging.basicConfig(level=logging.INFO, handlers=[file_handler])
+logging.basicConfig(
+    level=logging.INFO,
+    stream=sys.stdout,
+    format="%(asctime)s %(levelname)s %(message)s",
+)
 logger = logging.getLogger("inventory")
```

> 💡 로그 파일 로테이션, 보관, 검색은 이제 **플랫폼의 책임**입니다. 앱은 stdout 에 쓰기만 하면 됩니다.

## 2-3. 운영용 웹 서버와 DB 드라이버 추가 (`app/requirements.txt`)

```diff
 Flask==3.0.3
 Flask-SQLAlchemy==3.1.1
 SQLAlchemy==2.0.36
+psycopg2-binary==2.9.11
+gunicorn==23.0.0
```

- `gunicorn`: 운영용 WSGI 서버 (Flask 개발 서버 대체)
- `psycopg2-binary`: Lab 5 에서 쓸 PostgreSQL 드라이버

## 2-4. 로컬에서 동작 확인 (컨테이너 없이)

```bash
cd app
source .venv/bin/activate
pip install -r requirements.txt

# 환경 변수로 배너 색과 버전을 바꿔서 실행
APP_VERSION=1.1-local BANNER_COLOR="#8764b8" python app.py
```

배너가 **보라색**, version 이 `1.1-local` 이면 성공입니다. 이번에는 `app/logs/` 가 새로 생기지 않고 **로그가 터미널에 출력**됩니다. `Ctrl + C` 로 종료합니다.

## 2-5. Dockerfile 작성

`app/Dockerfile` 을 새로 만듭니다.

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 의존성 레이어를 먼저 설치해서 소스만 바뀔 때 빌드 캐시를 재사용
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# root 가 아닌 일반 사용자로 실행
RUN useradd --create-home appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# 컨테이너 1개당 프로세스 1개 + 스레드 8개. 확장은 워커 수가 아니라 "레플리카 수"로 합니다.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "8", "--access-logfile", "-", "app:app"]
```

`app/.dockerignore` 도 만듭니다. (로컬 DB 파일, 가상환경이 이미지에 들어가지 않도록)

```
__pycache__/
*.pyc
.venv/
venv/
data/
logs/
deploy-onprem/
.git
.env
```

### Dockerfile 핵심 포인트

| 항목 | 이유 |
|---|---|
| `requirements.txt` 를 먼저 COPY | 코드만 바꿀 때 `pip install` 레이어 캐시 재사용 → 빌드 속도 ↑ |
| `USER appuser` | 컨테이너 탈출 시 피해를 줄이는 최소 권한 원칙 |
| `gunicorn app:app` | `app.py` 의 `app` 객체를 운영용 서버로 실행 |
| `--workers 1 --threads 8` | 앱 시작 시 DB 초기화가 한 번만 실행되고, 동시성은 스레드로, 확장은 **레플리카**로 |
| `.dockerignore` 의 `data/` | 개발 PC 의 SQLite 파일이 이미지에 박히는 것을 방지 |

## 2-6. (선택) 로컬 컨테이너로 실행

Codespaces 또는 Docker 가 설치된 환경에서:

```bash
cd app
docker build -t inventory:local .
docker run --rm -p 8000:8000 -e APP_VERSION=container-local inventory:local
```

브라우저에서 포트 `8000` 을 열어 `version` 이 `container-local` 인지 확인합니다. `Ctrl + C` 로 종료.

> Docker 가 없다면 건너뛰세요. 다음 Lab 에서 Azure 가 대신 이미지를 빌드해 줍니다.

## ✅ 체크포인트
- [ ] `python app.py` 실행 시 환경 변수로 배너 색/버전이 바뀐다.
- [ ] 로그가 `app/logs/` 가 아니라 터미널에 출력된다.
- [ ] `app/Dockerfile`, `app/.dockerignore` 가 있다.
- [ ] 정답과 비교: `diff -r app solution -x data -x logs -x deploy-onprem -x .venv -x workflows -x __pycache__` 에서 큰 차이가 없다.

➡️ 다음: [Lab 3. Azure 리소스 만들기 & 이미지 빌드](lab3-azure-resources.md)
