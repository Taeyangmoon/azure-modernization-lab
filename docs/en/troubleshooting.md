# Troubleshooting

🌐 **English** | [한국어](../troubleshooting.md)

## General

| Symptom | Cause / fix |
|---|---|
| `$RG` etc. are empty in a new terminal | Re-run `source scripts/env.sh` (variables reset per terminal) |
| `az: 'containerapp' is not a known command` | `az extension add --name containerapp --upgrade` |
| `The subscription is not registered to use namespace 'Microsoft.App'` | Run the provider registration in [Lab 0-3](lab0-setup.md#0-3-register-resource-providers) |
| `AuthorizationFailed` | You need Contributor or higher on the subscription/resource group |
| Name conflict (ACR, PostgreSQL) | Delete `~/.aca-lab.env` and `source scripts/env.sh` to generate a new suffix (delete already-created resources first) |

## Labs 1–2 (local)

| Symptom | Fix |
|---|---|
| `Address already in use` (port 8080) | Stop the previously started app. macOS/Linux: find the PID with `lsof -ti:8080` and `kill <PID>` |
| `ModuleNotFoundError: flask` | Activate the virtualenv (`source .venv/bin/activate`) and `pip install -r requirements.txt` |
| `psycopg2` install fails (`pg_config not found`) | With an old local Python try `pip install --upgrade pip` and retry. Codespaces is recommended |
| `LOG_FILE` error after your edits | If you removed `LOG_FILE` from `config.py`, also remove every line in `app.py` that references `config.LOG_FILE` (see 2-2) |

## Lab 3 (ACR)

<a name="acr-tasks"></a>
### When your subscription doesn't allow ACR Tasks

Free/trial subscriptions may block `az acr build` (`TasksOperationsNotAllowed`). Build and push directly from an environment with Docker (Codespaces).

```bash
az acr login --name $ACR_NAME
docker build -t $ACR_NAME.azurecr.io/inventory:v1 ./app
docker push $ACR_NAME.azurecr.io/inventory:v1
```

## Lab 4 (deployment)

| Symptom | Fix |
|---|---|
| `UNAUTHORIZED` / image pull failure | AcrPull role assignment hasn't propagated. Retry after 1–2 min. Check with `az role assignment list --assignee <IDENTITY_PRINCIPAL> --scope $ACR_ID -o table` |
| Site shows `Application Error` / 502 | The container failed to start. Check `az containerapp logs show -n $APP_NAME -g $RG --tail 50` and the `--type system` logs. Make sure `--target-port` is **8000** |
| Environment is still `Provisioning` when creating the app | Wait 1–3 minutes for environment creation to finish, then re-run |

## Lab 5 (PostgreSQL)

| Symptom | Fix |
|---|---|
| `could not connect to server` / `timeout` (during migration) | Your IP isn't in the firewall. Re-run 5-3 (the IP changes if you restart Codespaces) |
| `no pg_hba.conf entry ... no encryption` | The connection string is missing `?sslmode=require` |
| Migration aborts with "already has data" | The app connected first and seeded sample data. Add `--truncate` |
| `duplicate key` when adding an item after migration | The sequence wasn't adjusted. The provided script does this automatically; a hand-written one needs `setval` |
| The app runs but `db backend` is still `sqlite` | Check that `DATABASE_URL=secretref:db-url` is set: `az containerapp show -n $APP_NAME -g $RG --query "properties.template.containers[0].env"` |
| No capacity in the region | Create the DB in another region by changing `--location` |
| Connection fails because of special characters in the password | `scripts/env.sh` generates an alphanumeric password. If you set your own, URL-encode it |

## Lab 6 (operations)

| Symptom | Fix |
|---|---|
| `ContainerAppConsoleLogs_CL` returns nothing | Log ingestion delay (2–5 min). Retry shortly |
| No scale-out | KEDA polls about every 30 s, so it lags. Keep the load running for 2+ minutes and use `--concurrency` of 100 or more |
| New revision gets no traffic | In multiple revision mode traffic must be assigned manually → `az containerapp ingress traffic set` |
| `--revision-weight` can't find the revision | Check exact names with `az containerapp revision list -n $APP_NAME -g $RG -o table` |

## Lab 7 (CI/CD)

| Symptom | Fix |
|---|---|
| `AADSTS70025` / `No matching federated identity record` | The federated credential `subject` must match `repo:<owner>/<repo>:ref:refs/heads/main` exactly (case-sensitive). Make sure your branch is `main` |
| `AuthorizationFailed` (workflow) | Check the service principal has Contributor on the resource group |
| Push doesn't trigger the workflow | Changed files must be under `app/**`, or use **Run workflow** on the Actions tab |
| Deployment succeeds but the page doesn't change | Multiple revision mode is still on → `az containerapp revision set-mode -n $APP_NAME -g $RG --mode single` |
| `gh secret set` returns 403 | Codespaces token permission issue. Use the web UI |
