# Baekjoon Weekly Problem Notifier

**한국어** · [日本語](README.ja.md) · [English](README.en.md)

> solved.ac API로 난이도별 백준 문제를 뽑아 **Discord 웹훅(@everyone)** 으로 주기적으로 보내주는 파이썬 스크립트입니다.

## 소개

`baekjoon_weekly.py` 하나로 동작하는 단일 파일 스크립트입니다. 실행되면 [solved.ac](https://solved.ac)의 문제 검색 API(`/api/v3/search/problem`)에서 난이도 구간별로 문제를 랜덤하게 선정하고, 아직 보내지 않은 문제만 골라 [백준(acmicpc.net)](https://www.acmicpc.net) 문제 링크와 함께 Discord 채널로 전송합니다. 스터디/동아리 채널에 매주 "이번 주 알고리즘 문제"를 자동으로 올려두는 용도로 만들었습니다.

한 번 실행 = 한 번 전송 구조이며, 주 1회 같은 주기 실행은 cron(리눅스) 등 외부 스케줄러에 맡깁니다.

## ✨ 주요 기능

- **난이도 구간별 랜덤 선정**: solved.ac tier 값을 기준으로 `easy`(tier 1\~8), `hard`(tier 9\~15) 두 구간에서 문제를 뽑습니다. 기본 분포는 `easy` 1문제 + `hard` 1문제로 매번 2문제를 선정합니다 (`DIFFICULTY_DISTRIBUTION`으로 조정 가능).
- **인기 문제 우선**: `acceptedUserCount`가 `MIN_ACCEPTED_USER_COUNT`(기본 1000) 이상인 "많이 풀린 문제"를 우선 사용하고, 충분치 않으면 조건을 단계적으로 완화하는 폴백 로직이 있습니다.
- **한글 문제 필터**: `ONLY_KOREAN_PROBLEMS = True`이면 `titleKo`(한글 제목)가 있는 문제만 선택합니다.
- **중복 방지**: 이미 보낸 문제 ID를 `used_problems.json`에 저장해, 다음 실행에서 최대한 겹치지 않게 제외합니다.
- **Discord 웹훅 전송**: `@everyone` 멘션과 함께 문제 번호 · 한글 제목 · solved.ac level · 백준 문제 URL을 정리해 메시지로 보냅니다.
- **환경 변수 기반 시크릿 관리**: 웹훅 URL을 코드에 넣지 않고 `.env` 파일 또는 환경 변수(`DISCORD_WEBHOOK_URL`)에서 읽어옵니다.

## 🛠 기술 스택

- **Python 3.9+** (`set[int]`, `list[dict]` 등 표준 제네릭 타입 힌트 사용)
- **requests** — solved.ac API 호출 및 Discord 웹훅 POST
- **solved.ac API v3** — 문제 데이터 소스
- **Discord Webhook** — 메시지 전송 대상

외부 의존성은 `requests` 하나뿐이며, `.env` 파싱은 별도 라이브러리 없이 직접 구현되어 있습니다.

## 🏗 동작 방식

1. `.env` 파일이 있으면 읽어 `os.environ`에 반영합니다.
2. `used_problems.json`에서 이전에 보낸 문제 ID 집합을 로드합니다.
3. `DIFFICULTY_DISTRIBUTION`의 각 구간별로 solved.ac 검색 API를 호출합니다.
   - 쿼리: `tier:{min}..{max}`, `sort=random`, `size=50`
   - 한글 문제 · 인기 문제 · 미사용 문제 순으로 필터링 후 필요한 개수만큼 샘플링
4. 선정된 문제로 Discord 메시지 문자열을 만들어 `DISCORD_WEBHOOK_URL`로 POST 전송합니다.
5. 이번에 보낸 문제 ID를 `used_problems.json`에 누적 저장합니다.

스케줄/트리거는 코드에 내장되어 있지 않습니다. 스크립트는 1회 실행형이며, 주기 실행은 cron 등으로 구성합니다(아래 참고).

### 설정값 (`baekjoon_weekly.py` 상단)

```python
ONLY_KOREAN_PROBLEMS = True          # titleKo가 있는 한글 문제만 사용
MIN_ACCEPTED_USER_COUNT = 1000       # "많이 풀린 문제" 기준 AC 유저 수
DIFFICULTY_DISTRIBUTION = {
    "easy": 1,   # tier 1~8 에서 1문제
    "hard": 1,   # tier 9~15 에서 1문제
}
TIER_RANGES = {
    "easy": (1, 8),
    "hard": (9, 15),
}
```

`DIFFICULTY_DISTRIBUTION`의 값을 늘리면(예: `easy` 2, `hard` 2) 한 번에 더 많은 문제를 보낼 수 있습니다.

## 🚀 시작하기

### 1. 요구 사항 및 설치

- Python 3.9 이상

```bash
pip install requests
```

### 2. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 만들고 Discord 웹훅 URL을 넣습니다. 코드에서 실제로 참조하는 변수는 다음 하나입니다.

```bash
# .env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxxxxxx/yyyyyyyy
```

`.env` 대신 셸 환경 변수로 `DISCORD_WEBHOOK_URL`을 직접 지정해도 됩니다. `.env` 파일은 Git에 커밋하지 않는 것을 권장합니다.

### 3. 실행

```bash
python baekjoon_weekly.py
```

성공하면 `@everyone 이번 주 백준 알고리즘 문제입니다 🎯` 메시지와 함께 선정된 문제들이 Discord 채널로 전송되고, `used_problems.json`이 갱신됩니다.

### 4. cron으로 주기 실행 (리눅스 서버 예시)

```bash
# 매주 월요일 09:00 실행
0 9 * * 1 /usr/bin/python3 /path/to/weekly_baekjoon/baekjoon_weekly.py >> /path/to/weekly_baekjoon/cron.log 2>&1
```

경로는 실제 배포 위치로 바꿔주세요. 서버에서도 `.env`(또는 환경 변수)를 동일하게 설정해야 합니다.

## 📁 파일 구조

```
weekly_baekjoon/
├── baekjoon_weekly.py   # 메인 스크립트 (문제 선정 → 메시지 생성 → 전송 → 기록)
├── used_problems.json   # 이미 보낸 문제 ID 저장 (실행 시 자동 생성/갱신)
├── .env                 # DISCORD_WEBHOOK_URL (직접 생성)
└── README.md
```

---

## 👤 기여도 & 개발 환경

| 항목 | 내용 |
|---|---|
| **기여 비율** | **100%** (단독 개발) |
| **커밋** | 7 / 7 (본인 / 전체 사람 커밋) |
| **참여 인원** | 1명 |

<sub>집계 기준(2026-08-12 스냅샷): origin의 **모든 브랜치**에서 도달 가능한 커밋(머지 커밋·빈 커밋 제외), 커밋 author 이메일 기준이며 동일인의 여러 이메일은 하나로 합산, 봇·자동화 커밋은 제외했습니다.</sub>
