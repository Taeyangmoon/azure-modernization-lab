# Lab 8. 리소스 정리 (5분)

🌐 [English](en/lab8-cleanup.md) | **한국어**

실습에서 만든 리소스는 비용이 발생합니다 (특히 PostgreSQL, ACR). **반드시 삭제**하세요.

## 8-1. Azure 리소스 삭제

리소스 그룹을 삭제하면 안에 있는 모든 리소스(Container App, 환경, ACR, PostgreSQL, Log Analytics, Managed Identity)가 함께 삭제됩니다.

```bash
source scripts/env.sh
az group delete --name $RG --yes --no-wait
```

삭제 확인 (몇 분 후 `false` 가 나오면 완료):

```bash
az group exists --name $RG
```

## 8-2. (Lab 7 을 했다면) Entra 앱 등록 삭제

```bash
APP_ID=$(az ad app list --display-name "gh-aca-lab-$SUFFIX" --query "[0].appId" -o tsv)
az ad app delete --id $APP_ID
```

GitHub 의 Secret/Variable(`AZURE_*`, `ACR_NAME`, `APP_NAME`, `RESOURCE_GROUP`)도 지우거나, 워크플로 파일 `.github/workflows/deploy.yml` 을 삭제해 두세요. (리소스가 없으면 푸시할 때마다 워크플로가 실패합니다.)

## 8-3. 로컬 정리

```bash
rm -f ~/.aca-lab.env          # 실습 변수(접미사, DB 비밀번호)
```

Codespaces 를 썼다면 <https://github.com/codespaces> 에서 Codespace 도 삭제합니다.

---

## 🎓 오늘 한 일 요약

| 단계 | Before (온프렘 VM) | After (Azure Container Apps) |
|---|---|---|
| 설정 | `config.py` 하드코딩 | 환경 변수 + Secret |
| 로그 | 파일 + SSH `tail -f` | stdout → Log Analytics (KQL) |
| 실행 | `python app.py` | gunicorn 컨테이너 이미지 |
| 데이터 | VM 디스크의 SQLite | PostgreSQL 관리형 DB (자동 백업) |
| 인증 | 비밀번호/계정 공유 | Managed Identity (ACR Pull), OIDC (CI/CD) |
| 확장 | VM 증설 (수 주) | HTTP 오토스케일 (수십 초), scale-to-zero |
| 배포 | scp + 재시작 (다운타임) | 리비전 + 트래픽 분할 + 즉시 롤백 |
| 릴리스 | 사람이 수작업 | GitHub Actions |

## 다음 단계

실제 운영 환경으로 가기 위해 추가로 고려할 것들입니다.

| 주제 | 설명 | 참고 |
|---|---|---|
| 네트워크 격리 | VNet 통합 + PostgreSQL Private Endpoint (공용 접근 제거) | [Container Apps 네트워킹](https://learn.microsoft.com/azure/container-apps/networking) |
| 비밀번호 없는 DB | Microsoft Entra 인증 + Managed Identity 로 PostgreSQL 접속 | [PostgreSQL Entra 인증](https://learn.microsoft.com/azure/postgresql/flexible-server/concepts-azure-ad-authentication) |
| 비밀 관리 | Azure Key Vault 참조 | [Container Apps Secrets](https://learn.microsoft.com/azure/container-apps/manage-secrets) |
| 헬스 프로브 | `/health` 를 Liveness/Readiness 프로브로 지정 | [Health probes](https://learn.microsoft.com/azure/container-apps/health-probes) |
| IaC | Bicep / Terraform / `azd` 로 모든 리소스 코드화 | [azd 템플릿](https://learn.microsoft.com/azure/developer/azure-developer-cli/) |
| 백그라운드 작업 | Container Apps **Jobs** (배치, 스케줄) | [Jobs](https://learn.microsoft.com/azure/container-apps/jobs) |
| 모니터링 | Application Insights / OpenTelemetry | [Observability](https://learn.microsoft.com/azure/container-apps/observability) |
| 사용자 인증 | Container Apps **Easy Auth** (Entra ID 로그인) | [Authentication](https://learn.microsoft.com/azure/container-apps/authentication) |
