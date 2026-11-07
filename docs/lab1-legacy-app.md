# Lab 1. 레거시 앱 실행하고 문제점 찾기 (15분)

🌐 [English](en/lab1-legacy-app.md) | **한국어**

## 목표
- "온프렘 VM 에서 돌던" 앱을 그대로 실행해 본다.
- 이 앱을 **그대로** 컨테이너/클라우드에 올리면 왜 문제가 되는지 **코드와 동작으로** 찾아낸다.

## 1-1. 앱 실행

`app/` 폴더가 온프렘 VM 에서 운영하던 앱입니다. 아래 명령은 **저장소 루트**에서 시작합니다.

```bash
cd app
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

- Codespaces: 하단 **PORTS** 탭에서 `8080` 포트의 🌐 아이콘을 눌러 엽니다.
- 로컬 PC: <http://localhost:8080>

> macOS 는 5000 포트를 AirPlay 가 쓰기 때문에 이 앱은 8080 을 사용합니다.

화면에서 아래를 해 봅니다.
1. 샘플 재고 12건이 보이는지 확인
2. **재고 등록** 폼으로 항목 1~2개 추가 (예: `테스트 장비`, 수량 5)
3. 화면 하단 **실행 환경 정보**의 `hostname`, `db backend` 확인 → `sqlite`

## 1-2. 앱이 어디에 무엇을 저장하는지 확인

새 터미널을 열고(앱은 계속 실행) 저장소 루트에서:

```bash
ls -la app/data app/logs
tail -5 app/logs/app.log
curl -s localhost:8080/health
```

- `app/data/inventory.db` → 재고 데이터가 **VM 로컬 디스크의 파일**에 저장됩니다.
- `app/logs/app.log` → 로그가 **VM 로컬 디스크의 파일**에 쌓입니다.

> 이 `inventory.db` 는 **Lab 5 에서 PostgreSQL 로 이전할 "운영 데이터"** 입니다. 삭제하지 마세요!

## 1-3. 문제점 찾기 (코드 리뷰)

`app/config.py` 와 `app/app.py` 를 열고 아래 질문에 답해 보세요.

| 질문 | 힌트 | 컨테이너/클라우드에서의 문제 |
|---|---|---|
| 1. DB 경로는 어디에 정의돼 있나? | `config.py` 의 `DATABASE_URL` | 환경별로 코드를 수정해야 한다. 비밀번호가 있다면 코드에 커밋된다. |
| 2. 로그는 어디로 가나? | `app.py` 상단 `RotatingFileHandler` | 컨테이너는 언제든 사라지고 파일도 같이 사라진다. 로그 수집 도구가 못 본다. |
| 3. 데이터는 어디에 저장되나? | `data/inventory.db` | 컨테이너가 재시작/복제되면 데이터가 사라지거나 인스턴스마다 달라진다. |
| 4. 어떤 서버로 실행하나? | `app.run(...)` | Flask 개발 서버는 운영용이 아니다 (운영 안정성, 보안/성능). |
| 5. 설정을 바꾸려면? | 버전/배너 색 | 코드 수정 → 재배포가 필요하다. |

## 1-4. 이 모든 것을 Twelve-Factor 관점으로

| Twelve-Factor 원칙 | 레거시 앱 | 현대화 목표 |
|---|---|---|
| III. Config — 설정은 환경에 | 코드에 하드코딩 | 환경 변수 |
| VI. Processes — 무상태 프로세스 | 로컬 파일/SQLite 에 상태 저장 | 외부 관리형 DB |
| XI. Logs — 로그는 이벤트 스트림 | 파일에 기록 | stdout |
| V. Build, release, run | scp + 수작업 | 이미지 + CI/CD |

## 1-5. 앱 종료

앱을 실행 중인 터미널에서 `Ctrl + C` 로 종료합니다.

`cd app` 으로 들어갔던 터미널은 `cd ..` 로 **저장소 루트**로 돌아옵니다. 이후 Lab의 명령도 저장소 루트에서 시작합니다.

## ✅ 체크포인트
- [ ] 브라우저에서 앱이 열리고, 항목을 추가할 수 있다.
- [ ] `app/data/inventory.db`, `app/logs/app.log` 파일이 생성되었다.
- [ ] 위 5가지 문제점을 설명할 수 있다.

➡️ 다음: [Lab 2. 코드 수정 + Dockerfile 작성](lab2-containerize.md)
