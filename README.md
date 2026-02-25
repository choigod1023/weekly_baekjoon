# Baekjoon Weekly Problem Notifier

주 1회, 백준 문제를 난이도 비율에 맞춰 뽑아서 **디스코드 웹훅(@everyone)** 으로 보내주는 간단한 파이썬 스크립트입니다.

## 기능

- solved.ac API를 이용해 **브론즈/실버/골드 난이도 비율**에 맞춰 문제를 선택
- 이미 한 번 보냈던 문제는 `used_problems.json`에 기록해 **최대한 중복을 피함**
- **한글 문제(titleKo 존재)** 만 선택하도록 옵션 제공
- 디스코드 웹훅 URL은 **`.env` 파일**에서 읽어와 코드/깃허브에 노출되지 않게 관리

## 1. 요구 사항

- Python 3.9 이상
- `requests` 라이브러리

```bash
pip install requests
```

## 2. 환경 변수(.env) 설정

프로젝트 루트(이 리포지토리 최상단)에 **`.env` 파일**을 만들고 다음 내용을 넣어주세요.

```bash
DISCORD_WEBHOOK_URL=여기에_디스코드_웹훅_URL
```

- 예시:

```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxxxxxx/yyyyyyyy
```

> `.env` 파일은 **절대 깃허브에 올리지 마세요.**  
> `.gitignore`에 `.env`를 추가해 두는 것을 추천합니다.

## 3. 스크립트 동작 방식

메인 스크립트는 `baekjoon_weekly.py` 입니다.

- `.env`에서 `DISCORD_WEBHOOK_URL`을 읽어와 디스코드 웹훅으로 메시지 전송
- `DIFFICULTY_DISTRIBUTION`으로 난이도 비율 설정
- `ONLY_KOREAN_PROBLEMS` 옵션으로 한글 문제만 사용할지 여부 설정
- 사용한 문제 ID는 `used_problems.json`에 저장

### 난이도 비율 설정

`baekjoon_weekly.py` 상단에서 수정할 수 있습니다.

```python
DIFFICULTY_DISTRIBUTION = {
    "bronze": 1,  # 브론즈 1문제
    "silver": 2,  # 실버 2문제
    "gold": 1,    # 골드 1문제
}
```

값을 변경해서 원하는 조합(예: 실버 3개, 골드 1개 등)으로 조정할 수 있습니다.

### 한글 문제만 사용할지 여부

```python
ONLY_KOREAN_PROBLEMS = True  # True면 titleKo가 있는 문제만 사용
```

`True`면 한글 제목이 있는 문제만 선택하려고 시도합니다.

## 4. 로컬에서 실행해 보기

```bash
python baekjoon_weekly.py
```

성공하면 디스코드 채널에 `@everyone 이번 주 백준 알고리즘 문제입니다` 메시지와 함께 문제 4개가 전송됩니다.

## 5. 리눅스 서버에서 크론으로 주 1회 실행

1. 이 리포지토리를 서버에 클론하거나 파일을 복사합니다.
2. 서버에서도 `.env` 파일을 같은 방식으로 설정합니다.
3. `crontab -e`로 크론을 열고, 예를 들어 **매주 월요일 09:00**에 실행하려면:

```bash
0 9 * * 1 /usr/bin/python3 /path/to/discordbaek/baekjoon_weekly.py >> /path/to/discordbaek/cron.log 2>&1
```

경로(`/path/to/discordbaek`)는 실제 프로젝트 경로로 바꿔주세요.

---

궁금한 점이나 기능을 더 추가하고 싶으면 이슈/PR 또는 질문으로 남겨 주세요.

