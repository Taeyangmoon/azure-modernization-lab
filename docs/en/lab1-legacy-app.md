# Lab 1. Run the legacy app and find its problems (15 min)

🌐 **English** | [한국어](../lab1-legacy-app.md)

## Goals
- Run the app exactly as it ran on the on-prem VM.
- Find — in the code and in its behavior — why it would be a problem to put it **as-is** into a container/the cloud.

## 1-1. Run the app

The `app/` folder is the app as it was operated on the on-prem VM.

```bash
cd app
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

- Codespaces: open the **PORTS** tab at the bottom and click the 🌐 icon next to port `8080`.
- Local PC: <http://localhost:8080>

> macOS uses port 5000 for AirPlay, so this app uses 8080.

> 🇰🇷 The UI is in Korean: 재고 등록 = *Register item*, 추가 = *Add*, 삭제 = *Delete*, 실행 환경 정보 = *Runtime info*.

In the browser:
1. Confirm the 12 sample inventory items are shown.
2. Add 1–2 items with the **Register item** form (e.g. `Test device`, quantity 5).
3. In **Runtime info** at the bottom, check `hostname` and `db backend` → `sqlite`.

## 1-2. See where the app stores things

Open a new terminal (leave the app running) and, from the repo root:

```bash
ls -la app/data app/logs
tail -5 app/logs/app.log
curl -s localhost:8080/health
```

- `app/data/inventory.db` → data lives in a **file on the VM's local disk**.
- `app/logs/app.log` → logs pile up in a **file on the VM's local disk**.

> This `inventory.db` is the **"production data" you will migrate to PostgreSQL in Lab 5**. Don't delete it!

## 1-3. Find the problems (code review)

Open `app/config.py` and `app/app.py` and answer:

| Question | Hint | Problem in containers / the cloud |
|---|---|---|
| 1. Where is the DB path defined? | `DATABASE_URL` in `config.py` | You must edit code per environment. Any password would be committed. |
| 2. Where do logs go? | `RotatingFileHandler` at the top of `app.py` | Containers disappear at any time, taking files with them. Log collectors can't see them. |
| 3. Where is data stored? | `data/inventory.db` | On restart/scale-out data is lost or differs per instance. |
| 4. Which server runs it? | `app.run(...)` | The Flask dev server isn't for production (single-threaded, security/perf). |
| 5. How do you change settings? | version / banner color | Edit code → redeploy. |

## 1-4. Through the Twelve-Factor lens

| Twelve-Factor principle | Legacy app | Modernization goal |
|---|---|---|
| III. Config — store config in the environment | Hard-coded | Environment variables |
| VI. Processes — stateless | State in local files / SQLite | External managed DB |
| XI. Logs — treat logs as event streams | Written to a file | stdout |
| V. Build, release, run | scp + manual steps | Image + CI/CD |

## 1-5. Stop the app

Press `Ctrl + C` in the terminal running the app.

## ✅ Checkpoint
- [ ] The app opens in the browser and you can add items.
- [ ] `app/data/inventory.db` and `app/logs/app.log` were created.
- [ ] You can explain the 5 problems above.

➡️ Next: [Lab 2. Code changes + write a Dockerfile](lab2-containerize.md)
