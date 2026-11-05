# Lab 2. Code changes + write a Dockerfile (30 min)

🌐 **English** | [한국어](../lab2-containerize.md)

## Goals
- Make **minimal changes** so the app follows cloud-native principles (config = env vars, logs = stdout).
- Add a production web server (gunicorn) and a **Dockerfile**.
- (Optional) Run the container locally.

> If you're stuck or short on time, copy files from `solution/` into `app/`.
> e.g. `cp solution/config.py app/config.py`

> 🇰🇷 Comments in the repo's source files are in Korean. The English comments below are translations — typing either is fine.

Do all the work in the `app/` folder.

## 2-1. Settings from environment variables (`app/config.py`)

**Replace** the entire contents of `app/config.py` with:

```python
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Falls back to a local SQLite file when DATABASE_URL is not set (local development)
# e.g. postgresql+psycopg2://user:password@host:5432/inventory
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "data", "inventory.db")
)

# Version / banner color shown on the page
APP_VERSION = os.environ.get("APP_VERSION", "1.0")
BANNER_COLOR = os.environ.get("BANNER_COLOR", "#0f6cbd")

PORT = int(os.environ.get("PORT", "8080"))
```

**What changed**: `LOG_FILE` is gone and every other value is read with `os.environ.get(name, default)`. Because of the defaults, local runs behave as before.

## 2-2. Logs to stdout (`app/app.py`)

Edit the imports and the logging setup at the top of `app.py`.

**(1) Imports** — remove the `RotatingFileHandler` line and add `sys`.

```diff
 import logging
 import os
 import socket
+import sys
 import time
 from datetime import datetime
-from logging.handlers import RotatingFileHandler
```

**(2) Logging setup** — replace the file-handler block (the section right below the "logging" comment banner, up to the line before `logger = ...`):

```diff
-os.makedirs(os.path.dirname(config.LOG_FILE), exist_ok=True)
-file_handler = RotatingFileHandler(config.LOG_FILE, maxBytes=1_000_000, backupCount=3)
-file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
-logging.basicConfig(level=logging.INFO, handlers=[file_handler])
+# Log to stdout instead of a file (Container Apps collects it and ships it to Log Analytics)
+logging.basicConfig(
+    level=logging.INFO,
+    stream=sys.stdout,
+    format="%(asctime)s %(levelname)s %(message)s",
+)
 logger = logging.getLogger("inventory")
```

> 💡 Log rotation, retention and search are now the **platform's job**. The app only writes to stdout.

## 2-3. Add a production web server and DB driver (`app/requirements.txt`)

```diff
 Flask==3.0.3
 Flask-SQLAlchemy==3.1.1
 SQLAlchemy==2.0.36
+psycopg2-binary==2.9.11
+gunicorn==23.0.0
```

- `gunicorn`: production WSGI server (replaces the Flask dev server)
- `psycopg2-binary`: PostgreSQL driver used in Lab 5

## 2-4. Verify locally (no container yet)

```bash
cd app
source .venv/bin/activate
pip install -r requirements.txt

# Change the banner color and version with environment variables
APP_VERSION=1.1-local BANNER_COLOR="#8764b8" python app.py
```

If the banner is **purple** and the version reads `1.1-local`, it works. Also, `app/logs/` is no longer created — **logs print to the terminal**. Stop with `Ctrl + C`.

## 2-5. Write the Dockerfile

Create `app/Dockerfile`:

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first so the layer is cached when only source changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as a non-root user
RUN useradd --create-home appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# One process + 8 threads per container. Scale by replicas, not by workers.
# (A single worker means DB initialization runs only once at startup)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "8", "--access-logfile", "-", "app:app"]
```

Also create `app/.dockerignore` (keeps local DB files and virtualenvs out of the image):

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

### Dockerfile key points

| Item | Why |
|---|---|
| `COPY requirements.txt` first | Reuses the `pip install` layer cache when only code changes → faster builds |
| `USER appuser` | Least privilege: limits damage if the container is compromised |
| `gunicorn app:app` | Runs the `app` object from `app.py` with a production server |
| `--workers 1 --threads 8` | DB init runs once at startup; concurrency via threads, scaling via **replicas** |
| `data/` in `.dockerignore` | Prevents your dev machine's SQLite file from being baked into the image |

## 2-6. (Optional) Run the container locally

In Codespaces or anywhere Docker is installed:

```bash
cd app
docker build -t inventory:local .
docker run --rm -p 8000:8000 -e APP_VERSION=container-local inventory:local
```

Open port `8000` in the browser and check that `version` is `container-local`. Stop with `Ctrl + C`.

> No Docker? Skip this. In the next lab Azure builds the image for you.

## ✅ Checkpoint
- [ ] With `python app.py`, env vars change the banner color/version.
- [ ] Logs print to the terminal instead of `app/logs/`.
- [ ] `app/Dockerfile` and `app/.dockerignore` exist.
- [ ] Compare with the solution: `diff -r app solution -x data -x logs -x deploy-onprem -x .venv -x workflows -x __pycache__` shows no significant differences (other than comments).

➡️ Next: [Lab 3. Create Azure resources & build the image](lab3-azure-resources.md)
