# 🚀 Modernize an On-Prem Python App to Azure Container Apps (Hands-on Lab)

🌐 **English** | [한국어](README.md)

In this lab you take a Flask app that used to run on an on-premises VM with `python app.py` and **containerize** it, deploy it to **Azure Container Apps**, and then add a **managed database (PostgreSQL)**, **autoscaling**, **zero-downtime releases** and **CI/CD**.

> ⏱️ Duration: ~2.5–3 hours (including the optional lab) · 💰 Cost: a few dollars at most; delete the resource group at the end

---

## What you will learn

| # | Topic | Key Azure services |
|---|-------|--------------------|
| 1 | Why a legacy app is hard to run in the cloud | - |
| 2 | Make the app cloud-native (env vars, stdout logs) + write a Dockerfile | Docker |
| 3 | Build the image & private registry | Azure Container Registry |
| 4 | Serverless container deployment | Azure Container Apps |
| 5 | Move local SQLite data to a managed DB, handle secrets | Azure Database for PostgreSQL |
| 6 | Logs, autoscaling, blue/green (traffic splitting) | Log Analytics, Revisions |
| 7 | (Optional) Push-to-deploy pipeline | GitHub Actions + OIDC |

## Architecture: Before → After

```mermaid
flowchart LR
  subgraph Before["Before: on-prem VM"]
    U1[User] --> VM["VM<br/>python app.py (dev server)<br/>hard-coded config.py"]
    VM --> SQLITE[("SQLite file<br/>(VM disk)")]
    VM --> LOGF[/"app.log file"/]
  end

  subgraph After["After: Azure"]
    U2[User] --> ING["Container Apps<br/>HTTPS ingress"]
    subgraph CAE["Container Apps environment"]
      ING --> R1["Replica 1<br/>gunicorn"]
      ING --> R2["Replica N<br/>(autoscale)"]
    end
    R1 --> PG[("Azure Database<br/>for PostgreSQL")]
    R2 --> PG
    R1 -. stdout logs .-> LAW[("Log Analytics")]
    ACR[("Azure Container<br/>Registry")] -. Managed Identity<br/>image pull .-> CAE
    GH["GitHub Actions"] -- "build & deploy" --> ACR
  end
```

### On-prem → Azure concept mapping

| On the on-prem VM… | On Container Apps… |
|---|---|
| Edit `config.py` by hand on every server | Inject **environment variables / secrets** (same code, different values) |
| `python app.py` dev server | Container image running **gunicorn** |
| SSH in and `tail -f` a log file | **stdout** → collected automatically into Log Analytics |
| SQLite on the VM disk | **Managed PostgreSQL** (backups/HA included) |
| One VM = fixed capacity, manual scaling | **Automatic replica scaling** (0 … N) |
| Manual deploy (scp, systemctl restart) | **Revisions** + traffic splitting, CI/CD |

## Sample app: Contoso Inventory

A small internal inventory web app built with Flask + SQLAlchemy. The footer shows **hostname / version / DB backend**, so you can *see* the effect of scale-out, revisions and the database switch.

> 🇰🇷 **Note:** The app UI labels, sample data and code comments are in Korean. UI cheat sheet: 재고 등록 = *Register item*, 품목명 = *Item name*, 수량 = *Quantity*, 보관 위치 = *Location*, 추가 = *Add*, 삭제 = *Delete*, 재고 목록 = *Inventory list*, 실행 환경 정보 = *Runtime info*.

## Repository layout

```
.
├── app/                    # ⭐ Lab starting point = the "on-prem VM" legacy app (you edit this)
│   ├── app.py  config.py  requirements.txt  templates/
│   └── deploy-onprem/      #   How the VM was operated (systemd unit, reference only)
├── solution/               # ✅ Reference solution (compare / copy when stuck). Includes Dockerfile + GitHub Actions template
├── tools/
│   ├── migrate_sqlite_to_postgres.py   # data migration script
│   └── loadtest.py                     # zero-install load generator
├── scripts/env.sh          # variables used across the lab (source it)
├── docs/                   # 📚 Lab guides in Korean (docs/en/ = English)
└── .devcontainer/          # GitHub Codespaces / Dev Container config
```

## Labs

| Lab | Title | Time |
|---|---|---|
| [Lab 0](docs/en/lab0-setup.md) | Environment setup (Codespaces, Azure login) | 15 min |
| [Lab 1](docs/en/lab1-legacy-app.md) | Run the legacy app and find its problems | 15 min |
| [Lab 2](docs/en/lab2-containerize.md) | Code changes + write a Dockerfile (containerize) | 30 min |
| [Lab 3](docs/en/lab3-azure-resources.md) | Create Azure resources & build the image (ACR) | 20 min |
| [Lab 4](docs/en/lab4-deploy.md) | Deploy to Container Apps & experience the "state problem" | 25 min |
| [Lab 5](docs/en/lab5-database.md) | Modernize data with PostgreSQL | 30 min |
| [Lab 6](docs/en/lab6-operate.md) | Logs · autoscaling · blue/green deployment | 30 min |
| [Lab 7](docs/en/lab7-cicd.md) | (Optional) CI/CD with GitHub Actions | 20 min |
| [Lab 8](docs/en/lab8-cleanup.md) | Clean up | 5 min |

Stuck? → [Troubleshooting](docs/en/troubleshooting.md)

## Prerequisites

- An **Azure subscription** (Contributor or higher, able to create resource groups)
- A **GitHub account** (Codespaces recommended — nothing to install)
- (If working locally) Python 3.10+, Azure CLI 2.60+, Docker (optional), Git

## Getting started

1. **Fork** this repository (needed for the Lab 7 CI/CD exercise).
2. In your fork: **Code → Codespaces → Create codespace on main**.
3. Start with [Lab 0](docs/en/lab0-setup.md).

> 💡 **Facilitator tip:** Every lab ends with a ✅ **checkpoint**. If someone can't pass it, have them compare with `solution/`. Creating PostgreSQL (Lab 5) takes 5–10 minutes, so start it before Lab 4 to save time.
