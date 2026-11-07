# Lab 0. 환경 준비 (15분)

🌐 [English](en/lab0-setup.md) | **한국어**

## 목표
- 실습 환경(Codespaces) 열기
- Azure 로그인 & 필요한 Resource Provider 등록
- 실습 변수 로드

## 0-1. 개발 환경 열기

**권장: GitHub Codespaces** (Python, Azure CLI, Docker, gh CLI 가 모두 설치되어 있습니다.)

1. 이 저장소를 **Fork** 합니다.
2. Fork 한 저장소 → **Code** → **Codespaces** → **Create codespace on main**
3. 터미널을 열고 도구를 확인합니다.

```bash
az version --query '"azure-cli"' -o tsv
python --version
docker --version
```

> 로컬 PC에서 진행하는 경우: Python 3.10+, [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli), Git 이 필요합니다. Docker 는 선택입니다 (이미지 빌드를 Azure 에서 하기 때문).
> 이 경우 아래 명령으로 확장을 설치하세요: `az extension add --name containerapp --upgrade`

## 0-2. Azure 로그인

```bash
az login --use-device-code
```

표시되는 코드를 브라우저에서 입력해 로그인합니다. 구독이 여러 개라면 실습에 사용할 구독을 선택합니다.

```bash
az account list -o table
az account set --subscription "<구독 이름 또는 ID>"
az account show --query "{name:name, id:id}" -o table
```

## 0-3. Resource Provider 등록

처음 쓰는 구독이면 아래 서비스 공급자를 등록해야 합니다. (이미 등록되어 있으면 바로 끝납니다.)

```bash
for ns in Microsoft.App Microsoft.OperationalInsights Microsoft.ContainerRegistry Microsoft.DBforPostgreSQL Microsoft.ManagedIdentity; do
  az provider register --namespace $ns --wait
done
```

## 0-4. 실습 변수 로드

```bash
source scripts/env.sh
```

출력 예시:

```
SUFFIX=a1b2c3  RG=rg-aca-lab-a1b2c3  ACR=acrlaba1b2c3  APP=ca-inventory  PG=pg-lab-a1b2c3
```

- 최초 실행 시 **고유 접미사**와 **DB 비밀번호**가 `~/.aca-lab.env` 에 저장됩니다. (ACR, DB 이름은 전 세계에서 유일해야 하기 때문)
- **새 터미널을 열 때마다 `source scripts/env.sh` 를 다시 실행**하세요.
- 리전을 바꾸고 싶다면 `export LOCATION=japaneast` 처럼 덮어쓰세요. (기본: `koreacentral`)
- 기존 실습과 분리하려면 **source 전에** `export LAB_ENV_FILE="$HOME/.aca-lab-validation.env"` 를 지정하세요. 새 터미널에서도 같은 경로를 지정하고, Lab 8에서 이 파일만 삭제합니다.

## ✅ 체크포인트

```bash
echo $RG $ACR_NAME
az account show --query name -o tsv
az provider show -n Microsoft.App --query registrationState -o tsv   # Registered
```

➡️ 다음: [Lab 1. 레거시 앱 실행하고 문제점 찾기](lab1-legacy-app.md)
