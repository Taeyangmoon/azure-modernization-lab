# 트러블슈팅

## 공통

| 증상 | 원인 / 해결 |
|---|---|
| 새 터미널에서 `$RG` 등이 비어 있음 | `source scripts/env.sh` 를 다시 실행 (변수는 터미널마다 초기화됨) |
| `az: 'containerapp' is not a known command` | `az extension add --name containerapp --upgrade` |
| `The subscription is not registered to use namespace 'Microsoft.App'` | [Lab 0-3](lab0-setup.md#0-3-resource-provider-등록) 의 Provider 등록 실행 |
| `AuthorizationFailed` | 구독/리소스 그룹에 Contributor 이상 권한이 필요 |
| 이름 중복 오류 (ACR, PostgreSQL) | `~/.aca-lab.env` 를 지우고 `source scripts/env.sh` 로 새 접미사 생성 (이미 만든 리소스가 있으면 먼저 삭제) |

## Lab 1~2 (로컬)

| 증상 | 해결 |
|---|---|
| `Address already in use` (포트 8080) | 이전에 실행한 앱을 종료. macOS/Linux: `lsof -ti:8080` 로 PID 확인 후 `kill <PID>` |
| `ModuleNotFoundError: flask` | 가상환경 활성화(`source .venv/bin/activate`) 후 `pip install -r requirements.txt` |
| `psycopg2` 설치 실패 (`pg_config not found`) | 로컬 Python 이 오래된 경우 `pip install --upgrade pip` 후 재시도. Codespaces 사용을 권장 |
| 수정한 코드에 `LOG_FILE` 에러 | `config.py` 에서 `LOG_FILE` 을 지웠다면 `app.py` 에서 `config.LOG_FILE` 을 참조하는 줄도 모두 지워야 함 (2-2 참고) |

## Lab 3 (ACR)

<a name="acr-tasks"></a>
### `ACR Tasks` 가 허용되지 않는 구독일 때

무료/체험 구독에서는 `az acr build` 가 막혀 있을 수 있습니다 (`TasksOperationsNotAllowed`). Docker 가 있는 환경(Codespaces)에서 직접 빌드/푸시하세요.

```bash
az acr login --name $ACR_NAME
docker build -t $ACR_NAME.azurecr.io/inventory:v1 ./app
docker push $ACR_NAME.azurecr.io/inventory:v1
```

## Lab 4 (배포)

| 증상 | 해결 |
|---|---|
| `UNAUTHORIZED` / 이미지 Pull 실패 | AcrPull 역할 할당 전파 지연. 1~2분 후 재시도. `az role assignment list --assignee <IDENTITY_PRINCIPAL> --scope $ACR_ID -o table` 로 확인 |
| 사이트가 `Application Error` / 502 | 컨테이너가 기동 실패. `az containerapp logs show -n $APP_NAME -g $RG --tail 50` 와 `--type system` 로그 확인. `--target-port` 가 **8000** 인지 확인 |
| 앱을 만들 때 환경이 `Provisioning` 상태 | 환경 생성이 끝날 때까지 1~3분 대기 후 재실행 |

## Lab 5 (PostgreSQL)

| 증상 | 해결 |
|---|---|
| `could not connect to server` / `timeout` (마이그레이션 시) | 방화벽에 내 IP 가 없음. 5-3 재실행 (Codespaces 를 재시작하면 IP 가 바뀜) |
| `no pg_hba.conf entry ... no encryption` | 접속 문자열에 `?sslmode=require` 누락 |
| 마이그레이션이 "이미 데이터가 있습니다" 로 중단 | 앱이 먼저 DB 에 접속해 샘플 데이터를 넣은 경우. `--truncate` 추가 |
| 이전 후 새 항목 추가 시 `duplicate key` | 시퀀스 미조정. 제공된 스크립트는 자동 처리하며, 직접 만든 스크립트라면 `setval` 필요 |
| 앱은 뜨는데 `db backend` 가 여전히 `sqlite` | `DATABASE_URL=secretref:db-url` 이 설정되었는지 확인: `az containerapp show -n $APP_NAME -g $RG --query "properties.template.containers[0].env"` |
| 리전에 용량이 없음 | `--location` 을 다른 리전으로 바꿔 DB 만 생성 |
| 비밀번호에 특수문자가 있어 접속 실패 | `scripts/env.sh` 가 영숫자만 쓰는 비밀번호를 생성. 직접 지정했다면 URL 인코딩 필요 |

## Lab 6 (운영)

| 증상 | 해결 |
|---|---|
| `ContainerAppConsoleLogs_CL` 결과가 비어 있음 | 로그 수집 지연(2~5분). 잠시 후 재시도 |
| 스케일 아웃이 안 됨 | KEDA 폴링 주기(약 30초) 때문에 지연. 부하를 2분 이상 유지하고 `--concurrency` 를 100 이상으로 |
| 새 리비전이 트래픽을 못 받음 | 다중 리비전 모드에서는 수동으로 트래픽 지정 필요 → `az containerapp ingress traffic set` |
| `--revision-weight` 에 지정한 리비전을 못 찾음 | `az containerapp revision list -n $APP_NAME -g $RG -o table` 로 정확한 이름 확인 |

## Lab 7 (CI/CD)

| 증상 | 해결 |
|---|---|
| `AADSTS70025` / `No matching federated identity record` | Federated Credential 의 `subject` 가 `repo:<소유자>/<저장소>:ref:refs/heads/main` 과 정확히 일치해야 함 (대소문자 포함). 브랜치가 `main` 인지 확인 |
| `AuthorizationFailed` (워크플로) | 서비스 주체에 리소스 그룹 Contributor 역할 할당 확인 |
| 푸시해도 워크플로가 안 돎 | 변경 파일이 `app/**` 에 있어야 함. 또는 Actions 탭에서 **Run workflow** 수동 실행 |
| 배포는 성공인데 화면이 안 바뀜 | 다중 리비전 모드가 남아 있음 → `az containerapp revision set-mode -n $APP_NAME -g $RG --mode single` |
| `gh secret set` 이 403 | Codespaces 토큰 권한 문제. 웹 UI 로 등록 |
