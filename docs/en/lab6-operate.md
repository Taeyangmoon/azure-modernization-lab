# Lab 6. Logs · autoscaling · blue/green deployment (30 min)

🌐 **English** | [한국어](../lab6-operate.md)

## Goals
- Query logs in **Log Analytics** instead of log files.
- Watch **autoscaling** on **concurrent HTTP requests** with a load test.
- Release a new version safely with **revisions** and **traffic splitting**, and roll back instantly.

```bash
source scripts/env.sh
APP_URL=https://$(az containerapp show -n $APP_NAME -g $RG --query properties.configuration.ingress.fqdn -o tsv)
echo $APP_URL
```

---

## 6-1. Query logs

### (1) Live stream

In terminal A:

```bash
az containerapp logs show -n $APP_NAME -g $RG --follow --tail 10
```

In terminal B (or the browser) add/delete items. `Item added: ...` and `Item deleted: ...` appear immediately. When done, press `Ctrl + C` in terminal A.

### (2) Log Analytics query (KQL)

It can take **2–5 minutes** for console logs to reach Log Analytics.

```bash
LAW_ID=$(az monitor log-analytics workspace show -g $RG -n $LAW_NAME --query customerId -o tsv)

az monitor log-analytics query \
  --workspace $LAW_ID \
  --analytics-query "ContainerAppConsoleLogs_CL
    | where ContainerAppName_s == '$APP_NAME'
    | where Log_s has 'Item'
    | project TimeGenerated, RevisionName_s, Log_s
    | order by TimeGenerated desc
    | take 20" \
  -o table
```

> If asked to install the `log-analytics` extension on first run, answer `Y`.

**In the Azure Portal**: Container App → **Monitoring → Logs**; paste the KQL part of the command above. Compare it with `grep app.log` on the old VM.

---

## 6-2. Autoscaling (on concurrent HTTP requests)

### Set the scale rule

> Add replicas when one replica exceeds **10 concurrent requests** (min 1, max 5).

```bash
az containerapp update \
  --name $APP_NAME \
  --resource-group $RG \
  --min-replicas 1 \
  --max-replicas 5 \
  --scale-rule-name http-scale \
  --scale-rule-type http \
  --scale-rule-http-concurrency 10 \
  -o none
```

### Generate load

Terminal A: watch the replica count

```bash
watch -n 5 "az containerapp replica list -n $APP_NAME -g $RG --query '[].name' -o tsv"
```

(No `watch`? Run `az containerapp replica list -n $APP_NAME -g $RG -o table` yourself every few seconds.)

Terminal B: 100 concurrent requests for 2 minutes

```bash
python3 tools/loadtest.py $APP_URL --duration 120 --concurrency 100
```

**Observe**
- **30–60 seconds** after the load starts, replicas go 2 → 3 → … up to 5.
- The **"Replicas that responded"** line in the `loadtest.py` result matches the number of replicas. (Requests were spread over several instances.)
- About **5 minutes** after the load stops, it scales back in to 1 (scale-in cooldown).

> 💡 **Scale to zero**: with `--min-replicas 0` the app has zero replicas when idle, so the **cost is zero** (at the price of a cold start on the first request). Great for dev/test or occasionally used apps. We keep 1 in this lab.

> On the on-prem VM? You'd have bought servers for peak load up front, or waited weeks for more capacity.

---

## 6-3. Revisions & blue/green deployment

A **revision** is an **immutable snapshot** of a container app. Every change to settings such as the image or env vars creates a new revision. In **multiple revision mode** several revisions run side by side and you can split traffic by percentage.

### (1) Switch to multiple revision mode and pin the current version (blue)

```bash
az containerapp revision set-mode -n $APP_NAME -g $RG --mode multiple

REV_BLUE=$(az containerapp show -n $APP_NAME -g $RG --query properties.latestRevisionName -o tsv)
echo "blue = $REV_BLUE"

# Pin 100% of traffic to blue so new revisions don't take traffic automatically
az containerapp ingress traffic set -n $APP_NAME -g $RG --revision-weight $REV_BLUE=100 -o table
```

### (2) Deploy the new version (green) — 0% traffic

Keep the same image, but create a new revision with **only the version label and banner color changed**.

```bash
az containerapp update \
  --name $APP_NAME \
  --resource-group $RG \
  --revision-suffix green \
  --set-env-vars APP_VERSION=3.0-green BANNER_COLOR="#107c10" \
  -o none

az containerapp revision list -n $APP_NAME -g $RG \
  --query "[].{name:name, active:properties.active, traffic:properties.trafficWeight}" -o table
```

The `green` revision shows **traffic 0**. The new version is ready without affecting any user.

### (3) Canary: split traffic 80 / 20

```bash
az containerapp ingress traffic set -n $APP_NAME -g $RG \
  --revision-weight $REV_BLUE=80 ${APP_NAME}--green=20 -o table

for i in $(seq 1 30); do curl -s $APP_URL/health | grep -o '"version":"[^"]*"'; done | sort | uniq -c
```

Expected (roughly):

```
 24 "version":"2.0-pg"
  6 "version":"3.0-green"
```

Refreshing the browser shows a mix of **blue banners (old)** and **green banners (new)**.

### (4) Trouble! Roll back immediately

```bash
az containerapp ingress traffic set -n $APP_NAME -g $RG --revision-weight $REV_BLUE=100 -o table
```

Refresh and everything is blue again — a rollback in seconds, **without redeploying**.

### (5) All good? Promote → return to single revision mode

```bash
az containerapp ingress traffic set -n $APP_NAME -g $RG --revision-weight ${APP_NAME}--green=100 -o table
az containerapp revision set-mode -n $APP_NAME -g $RG --mode single
```

> ⚠️ If you'll do **Lab 7 (CI/CD)**, you must be back in **single revision mode** so new deployments automatically get 100% of traffic.

---

## ✅ Checkpoint
- [ ] You queried app logs with `ContainerAppConsoleLogs_CL`.
- [ ] Replicas scaled to 2 or more during the load test.
- [ ] In the 80/20 split, both versions answered.
- [ ] You understand rolling back to blue and promoting green.

➡️ Next: [Lab 7. (Optional) CI/CD with GitHub Actions](lab7-cicd.md) or [Lab 8. Clean up](lab8-cleanup.md)
