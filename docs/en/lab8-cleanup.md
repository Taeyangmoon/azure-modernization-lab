# Lab 8. Clean up (5 min)

🌐 **English** | [한국어](../lab8-cleanup.md)

The resources you created cost money (especially PostgreSQL and ACR). **Be sure to delete them.**

## 8-1. Delete the Azure resources

Deleting the resource group deletes everything in it (Container App, environment, ACR, PostgreSQL, Log Analytics, Managed Identity).

```bash
source scripts/env.sh
az group delete --name $RG --yes --no-wait
```

Confirm (when it prints `false` a few minutes later, it's done):

```bash
az group exists --name $RG
```

## 8-2. (If you did Lab 7) Delete the Entra app registration

```bash
APP_ID=$(az ad app list --display-name "gh-aca-lab-$SUFFIX" --query "[0].appId" -o tsv)
az ad app delete --id $APP_ID
```

Also remove the GitHub secrets/variables (`AZURE_*`, `ACR_NAME`, `APP_NAME`, `RESOURCE_GROUP`), or delete `.github/workflows/deploy.yml`. (Once the resources are gone, the workflow would fail on every push.)

## 8-3. Local cleanup

```bash
rm -f "$LAB_ENV_FILE"        # this run's lab variables (suffix, DB password)
```

If you used Codespaces, also delete the codespace at <https://github.com/codespaces>.

---

## 🎓 Summary of what you did

| Area | Before (on-prem VM) | After (Azure Container Apps) |
|---|---|---|
| Config | Hard-coded `config.py` | Env vars + secrets |
| Logs | Files + SSH `tail -f` | stdout → Log Analytics (KQL) |
| Runtime | `python app.py` | gunicorn container image |
| Data | SQLite on VM disk | Managed PostgreSQL (automatic backups) |
| Auth | Shared passwords/accounts | Managed Identity (ACR pull), OIDC (CI/CD) |
| Scaling | Add VMs (weeks) | HTTP autoscale (seconds), scale-to-zero |
| Deployment | scp + restart (downtime) | Revisions + traffic split + instant rollback |
| Release | Manual | GitHub Actions |

## Next steps

Things to consider on the way to a real production setup.

| Topic | Description | Reference |
|---|---|---|
| Network isolation | VNet integration + PostgreSQL Private Endpoint (remove public access) | [Container Apps networking](https://learn.microsoft.com/azure/container-apps/networking) |
| Passwordless DB | Connect to PostgreSQL with Microsoft Entra auth + Managed Identity | [PostgreSQL Entra authentication](https://learn.microsoft.com/azure/postgresql/flexible-server/concepts-azure-ad-authentication) |
| Secret management | Azure Key Vault references | [Container Apps secrets](https://learn.microsoft.com/azure/container-apps/manage-secrets) |
| Health probes | Use `/health` as liveness/readiness probes | [Health probes](https://learn.microsoft.com/azure/container-apps/health-probes) |
| IaC | Codify everything with Bicep / Terraform / `azd` | [azd](https://learn.microsoft.com/azure/developer/azure-developer-cli/) |
| Background work | Container Apps **Jobs** (batch, scheduled) | [Jobs](https://learn.microsoft.com/azure/container-apps/jobs) |
| Monitoring | Application Insights / OpenTelemetry | [Observability](https://learn.microsoft.com/azure/container-apps/observability) |
| User authentication | Container Apps **Easy Auth** (Entra ID sign-in) | [Authentication](https://learn.microsoft.com/azure/container-apps/authentication) |
