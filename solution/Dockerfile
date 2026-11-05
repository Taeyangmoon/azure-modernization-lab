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
# (워커를 1개로 두면 시작 시 DB 초기화가 한 번만 실행됩니다)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "8", "--access-logfile", "-", "app:app"]
