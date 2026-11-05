#!/usr/bin/env bash
# 실습 전체에서 쓰는 변수를 한 번에 정의합니다.
# 사용법:  source scripts/env.sh      (새 터미널을 열 때마다 다시 실행)
#
# 최초 1회 실행 시 고유 접미사(suffix)와 DB 비밀번호를 생성해 ~/.aca-lab.env 에 저장하므로,
# 터미널을 다시 열어도 같은 이름/비밀번호가 재사용됩니다.

LAB_ENV_FILE="${HOME}/.aca-lab.env"

if [ ! -f "$LAB_ENV_FILE" ]; then
  SUFFIX="$(openssl rand -hex 3)"                      # 예: a1b2c3 (ACR/DB 이름 중복 방지)
  PG_PASSWORD="Lab$(openssl rand -hex 8)x9"            # 영문+숫자만 사용 (URL 인코딩 이슈 방지)
  cat > "$LAB_ENV_FILE" <<EOF
SUFFIX=$SUFFIX
PG_PASSWORD=$PG_PASSWORD
EOF
  chmod 600 "$LAB_ENV_FILE"
fi
# shellcheck disable=SC1090
source "$LAB_ENV_FILE"

export LOCATION="koreacentral"
export RG="rg-aca-lab-${SUFFIX}"
export ACR_NAME="acrlab${SUFFIX}"
export LAW_NAME="law-aca-lab"
export ENV_NAME="cae-aca-lab"
export APP_NAME="ca-inventory"
export IDENTITY_NAME="id-inventory"
export PG_SERVER="pg-lab-${SUFFIX}"
export PG_ADMIN="pgadmin"
export PG_DB="inventory"
export PG_PASSWORD

echo "SUFFIX=$SUFFIX  RG=$RG  ACR=$ACR_NAME  APP=$APP_NAME  PG=$PG_SERVER"
