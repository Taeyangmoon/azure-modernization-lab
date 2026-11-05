# Lab 0. Environment setup (15 min)

🌐 **English** | [한국어](../lab0-setup.md)

## Goals
- Open the lab environment (Codespaces)
- Sign in to Azure & register the required resource providers
- Load the lab variables

## 0-1. Open the dev environment

**Recommended: GitHub Codespaces** (Python, Azure CLI, Docker and the gh CLI are preinstalled.)

1. **Fork** this repository.
2. In your fork: **Code** → **Codespaces** → **Create codespace on main**
3. Open a terminal and check the tools.

```bash
az version --query '"azure-cli"' -o tsv
python --version
docker --version
```

> Working locally? You need Python 3.10+, the [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) and Git. Docker is optional (images are built in Azure).
> Install the extension with: `az extension add --name containerapp --upgrade`

## 0-2. Sign in to Azure

```bash
az login --use-device-code
```

Enter the displayed code in your browser. If you have several subscriptions, pick the one for this lab.

```bash
az account list -o table
az account set --subscription "<subscription name or ID>"
az account show --query "{name:name, id:id}" -o table
```

## 0-3. Register resource providers

On a fresh subscription you must register these providers (it's instant if they already are).

```bash
for ns in Microsoft.App Microsoft.OperationalInsights Microsoft.ContainerRegistry Microsoft.DBforPostgreSQL; do
  az provider register --namespace $ns --wait
done
```

## 0-4. Load the lab variables

```bash
source scripts/env.sh
```

Example output:

```
SUFFIX=a1b2c3  RG=rg-aca-lab-a1b2c3  ACR=acrlaba1b2c3  APP=ca-inventory  PG=pg-lab-a1b2c3
```

- On first run a **unique suffix** and a **DB password** are saved to `~/.aca-lab.env` (ACR and DB names must be globally unique).
- **Re-run `source scripts/env.sh` in every new terminal.**
- To change the region: `export LOCATION=japaneast` (default: `koreacentral`).

## ✅ Checkpoint

```bash
echo $RG $ACR_NAME
az account show --query name -o tsv
az provider show -n Microsoft.App --query registrationState -o tsv   # Registered
```

➡️ Next: [Lab 1. Run the legacy app and find its problems](lab1-legacy-app.md)
