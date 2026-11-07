# Lab 6. 로그 · 오토스케일 · 블루/그린 배포 (30분)

🌐 [English](en/lab6-operate.md) | **한국어**

## 목표
- 파일 로그 대신 **Log Analytics** 로 로그를 조회한다.
- **HTTP 동시 요청 수** 기준 **오토스케일**이 동작하는 것을 부하 테스트로 확인한다.
- **리비전**과 **트래픽 분할**로 위험 없이 새 버전을 배포하고, 즉시 롤백한다.

```bash
source scripts/env.sh
APP_URL=https://$(az containerapp show -n $APP_NAME -g $RG --query properties.configuration.ingress.fqdn -o tsv)
echo $APP_URL
```

---

## 6-1. 로그 조회

### (1) 실시간 스트림

터미널 A 에서:

```bash
az containerapp logs show -n $APP_NAME -g $RG --follow --tail 10
```

터미널 B(또는 브라우저)에서 항목을 추가/삭제해 보세요. `Item added: ...`, `Item deleted: ...` 로그가 바로 보입니다. 확인했으면 터미널 A 에서 `Ctrl + C`.

### (2) Log Analytics 쿼리 (KQL)

콘솔 로그가 Log Analytics 로 수집되기까지 **2~5분** 걸릴 수 있습니다.

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

> 처음 실행 시 확장 설치(`log-analytics`) 여부를 물으면 `Y` 를 입력하세요.

**Azure Portal 에서 보기**: Container App → **Monitoring → Logs** 에서 같은 쿼리(`az` 명령 안의 KQL 부분)를 붙여넣어 실행할 수 있습니다. 온프렘에서 `grep app.log` 하던 것과 비교해 보세요.

---

## 6-2. 오토스케일 (HTTP 동시 요청 기준)

### 스케일 규칙 설정

> 레플리카 1개가 **동시 요청 10개**를 넘기면 레플리카를 추가 (최소 1, 최대 5).

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

### 부하 발생

터미널 A: 레플리카 수 관찰

```bash
watch -n 5 "az containerapp replica list -n $APP_NAME -g $RG --query '[].name' -o tsv"
```

(`watch` 가 없으면 몇 초 간격으로 `az containerapp replica list -n $APP_NAME -g $RG -o table` 를 직접 실행)

터미널 B: 2분간 동시 요청 100개

```bash
python3 tools/loadtest.py $APP_URL --duration 120 --concurrency 100
```

성공 응답이 있고 오류가 없을 때만 종료 코드가 `0` 입니다. 연결 실패·HTTP 오류·비정상 `/health` 응답은 실패로 집계하고 원인을 출력합니다. 오류가 있으면 앱 로그와 상태를 확인한 뒤 다시 실행하세요.

**관찰**
- 부하가 시작되고 **30~60초 뒤** 레플리카가 2 → 3 → … 최대 5개로 늘어납니다.
- `loadtest.py` 결과의 **"응답한 레플리카 수"** 가 늘어난 레플리카 수와 비슷합니다. (요청이 여러 인스턴스에 분산됨. 스케일 규칙 적용 직후에는 이전 리비전의 레플리카가 잠깐 포함되어 1~2개 더 보일 수 있음)
- 부하를 멈추면 약 **5분 후** 다시 1개로 줄어듭니다 (scale-in 쿨다운).

> 💡 **Scale to zero**: `--min-replicas 0` 으로 설정하면 요청이 없을 때 레플리카가 0개가 되어 **앱의 레플리카 실행 비용이 발생하지 않습니다**. ACR·PostgreSQL·로그 등의 비용은 계속 발생합니다. (대신 첫 요청에 콜드 스타트 지연) 개발/테스트 환경이나 간헐적 사용 앱에 유용합니다. 이 실습에서는 1로 유지합니다.

> 온프렘 VM 이라면? 피크 대비 서버를 미리 사 두거나, 증설에 수 주가 걸렸을 것입니다.

---

## 6-3. 리비전 & 블루/그린 배포

**리비전(Revision)** 은 컨테이너 앱의 **불변 스냅샷**입니다. 이미지·환경 변수 같은 설정이 바뀔 때마다 새 리비전이 만들어집니다. **다중 리비전 모드**에서는 여러 리비전을 동시에 띄우고 트래픽을 비율로 나눌 수 있습니다.

### (1) 다중 리비전 모드로 전환하고 현재 버전(blue) 고정

```bash
az containerapp revision set-mode -n $APP_NAME -g $RG --mode multiple

REV_BLUE=$(az containerapp show -n $APP_NAME -g $RG --query properties.latestRevisionName -o tsv)
echo "blue = $REV_BLUE"

# 새 리비전이 생겨도 트래픽이 자동으로 넘어가지 않도록 blue 에 100% 고정
az containerapp ingress traffic set -n $APP_NAME -g $RG --revision-weight $REV_BLUE=100 -o table
```

### (2) 새 버전(green) 배포 — 트래픽 0%

이미지는 그대로 두고 **버전 표시와 배너 색만 바꾼** 새 리비전을 만듭니다.

```bash
az containerapp update \
  --name $APP_NAME \
  --resource-group $RG \
  --revision-suffix green \
  --set-env-vars APP_VERSION=3.0-green BANNER_COLOR="#107c10" \
  -o none

az containerapp revision list -n $APP_NAME -g $RG \
  --query "[].{name:name, active:properties.active, traffic:properties.trafficWeight, health:properties.healthState}" -o table
```

`green` 리비전의 **traffic은 0** 입니다. `health` 가 아직 `None` 이면 준비 중이므로 위 조회를 다시 실행해 **`Healthy` 인 것을 확인한 뒤** 트래픽을 분할하세요. 사용자 영향 없이 새 버전을 준비할 수 있습니다.

### (3) 카나리: 80 / 20 으로 트래픽 분할

```bash
az containerapp ingress traffic set -n $APP_NAME -g $RG \
  --revision-weight $REV_BLUE=80 ${APP_NAME}--green=20 -o table

for i in $(seq 1 30); do curl -s $APP_URL/health | grep -o '"version":"[^"]*"'; done | sort | uniq -c
```

예상 결과 (대략):

```
 24 "version":"2.0-pg"
  6 "version":"3.0-green"
```

브라우저를 여러 번 새로고침하면 **파란 배너(기존)** 와 **초록 배너(신규)** 가 섞여 보입니다.

### (4) 문제 발생! 즉시 롤백

```bash
az containerapp ingress traffic set -n $APP_NAME -g $RG --revision-weight $REV_BLUE=100 -o table
```

새로고침하면 바로 전부 파란 배너로 돌아옵니다. **재배포 없이 몇 초 만에** 롤백됩니다.

### (5) 문제 없다면 승격 → 단일 리비전 모드 복귀

```bash
az containerapp ingress traffic set -n $APP_NAME -g $RG --revision-weight ${APP_NAME}--green=100 -o table
az containerapp revision set-mode -n $APP_NAME -g $RG --mode single
```

> ⚠️ **Lab 7(CI/CD)** 을 진행한다면 반드시 **단일 리비전 모드**로 돌아와 있어야 새 배포가 자동으로 100% 트래픽을 받습니다.

---

## ✅ 체크포인트
- [ ] `ContainerAppConsoleLogs_CL` 쿼리로 앱 로그를 조회했다.
- [ ] 부하 테스트 중 레플리카가 2개 이상으로 늘어났다.
- [ ] 80/20 분할에서 두 버전이 섞여 응답하는 것을 확인했다.
- [ ] blue 로 롤백했다가 green 으로 승격하는 흐름을 이해했다.

➡️ 다음: [Lab 7. (선택) GitHub Actions CI/CD](lab7-cicd.md) 또는 [Lab 8. 정리](lab8-cleanup.md)
