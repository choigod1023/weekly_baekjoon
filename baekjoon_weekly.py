import json
import os
import random
import requests

# ==============================
# 설정 영역
# ==============================

# 디스코드 웹훅 URL은 코드에 직접 적지 않고
# .env 파일의 DISCORD_WEBHOOK_URL 환경 변수에서 읽어옵니다.

# 한글 문제만 사용할지 여부
# - True 로 두면 titleKo 가 비어 있지 않은 문제만 사용합니다.
ONLY_KOREAN_PROBLEMS = True

# 난이도별 문제 개수 설정
# - 총합이 이번 주에 풀 문제 개수가 됩니다. (현재 4문제)
# - solved.ac 기준 level:
#   - 브론즈: 1~5
#   - 실버  : 6~10
#   - 골드  : 11~15
DIFFICULTY_DISTRIBUTION = {
    "bronze": 1,  # 브론즈 1문제
    "silver": 2,  # 실버 2문제
    "gold": 1,    # 골드 1문제
}

# 난이도별 level 범위 매핑
TIER_RANGES = {
    "bronze": (1, 5),
    "silver": (6, 10),
    "gold": (11, 15),
}

# 한 번에 solved.ac에서 가져올 최대 문제 수
# - 이미 낸 문제를 제외해야 하므로, 필요한 수보다 넉넉하게 요청합니다.
SOLVED_AC_FETCH_SIZE = 50

# 이전에 보냈던 문제 ID를 저장할 파일 경로 (스크립트와 같은 폴더에 생성)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USED_PROBLEMS_FILE = os.path.join(BASE_DIR, "used_problems.json")

# .env 파일 경로 (.git에는 올리지 말 것)
ENV_PATH = os.path.join(BASE_DIR, ".env")

# solved.ac 문제 검색 API 엔드포인트
SOLVED_AC_SEARCH_URL = "https://solved.ac/api/v3/search/problem"


# ==============================
# 내부 유틸 함수들
# ==============================

def load_env_from_file() -> None:
    """
    .env 파일이 있으면 읽어서 os.environ에 반영한다.
    - 형식 예시: DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
    """
    if not os.path.exists(ENV_PATH):
        return

    try:
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key:
                    os.environ.setdefault(key, value)
    except Exception:
        # .env 파싱 실패는 치명적이지 않으므로 조용히 무시
        pass


def load_used_problems() -> set[int]:
    """이전에 디스코드에 보냈던 문제 ID 집합을 읽어온다."""
    if not os.path.exists(USED_PROBLEMS_FILE):
        return set()

    try:
        with open(USED_PROBLEMS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # JSON에는 리스트 형태로 저장한다고 가정
            return set(int(x) for x in data)
    except Exception:
        # 파일이 깨졌거나 포맷이 잘못된 경우, 안전하게 새로 시작
        return set()


def save_used_problems(used_ids: set[int]) -> None:
    """지금까지 사용한 문제 ID 집합을 파일로 저장한다."""
    with open(USED_PROBLEMS_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(list(used_ids)), f, ensure_ascii=False, indent=2)


def fetch_problems_by_tier_range(min_tier: int, max_tier: int, used_ids: set[int], need_count: int) -> list[dict]:
    """
    특정 난이도 구간에서 아직 사용하지 않은 문제들을 가져온다.
    - solved.ac에서 random 정렬로 여러 문제를 받아오고,
    - 이미 낸 문제(used_ids)는 최대한 제외해서 반환한다.
    """
    params = {
        "query": f"tier:{min_tier}..{max_tier}",
        "page": 1,
        "sort": "random",
        "direction": "desc",
        "size": SOLVED_AC_FETCH_SIZE,
    }

    resp = requests.get(SOLVED_AC_SEARCH_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    items = data.get("items", [])

    # 한글 문제만 사용할 경우, titleKo 가 있는 문제만 남긴다.
    if ONLY_KOREAN_PROBLEMS:
        items = [p for p in items if p.get("titleKo")]

    # 우선 이미 사용한 문제를 제외
    filtered = [p for p in items if p.get("problemId") not in used_ids]

    if len(filtered) >= need_count:
        # 충분히 많으면 그 중에서만 뽑기
        return random.sample(filtered, need_count)

    # 아직 충분치 않은 경우:
    # 1차로 filtered 전부 사용
    selected = filtered.copy()

    # 그래도 부족하면, 이미 사용한 문제도 허용해서 items에서 채운다.
    remaining = need_count - len(selected)
    if remaining > 0:
        # 이미 선택된 문제는 제외하고 랜덤으로 더 뽑기
        already_ids = {p.get("problemId") for p in selected}
        candidates = [p for p in items if p.get("problemId") not in already_ids]

        if len(candidates) <= remaining:
            selected.extend(candidates)
        else:
            selected.extend(random.sample(candidates, remaining))

    return selected


def fetch_problems_with_distribution(distribution: dict[str, int], used_ids: set[int]) -> list[dict]:
    """
    난이도 비율 설정(distribution)에 맞게 전체 문제 리스트를 만든다.
    예) {"silver": 2, "gold": 1} 라면
        - 실버 구간에서 2개
        - 골드 구간에서 1개
    """
    all_selected: list[dict] = []
    globally_selected_ids: set[int] = set()

    for tier_name, count in distribution.items():
        if count <= 0:
            continue

        if tier_name not in TIER_RANGES:
            raise ValueError(f"알 수 없는 난이도 키: {tier_name}")

        min_tier, max_tier = TIER_RANGES[tier_name]

        # 전역적으로 이미 선택된 문제도 제외해야 중복이 안 생긴다.
        effective_used_ids = used_ids.union(globally_selected_ids)

        selected = fetch_problems_by_tier_range(
            min_tier=min_tier,
            max_tier=max_tier,
            used_ids=effective_used_ids,
            need_count=count,
        )

        all_selected.extend(selected)
        globally_selected_ids.update(p.get("problemId") for p in selected)

    return all_selected


def build_discord_message(problems: list[dict]) -> str:
    """디스코드에 보낼 메시지 문자열을 만든다."""
    total = len(problems)
    lines: list[str] = []

    lines.append("@everyone 이번 주 백준 알고리즘 문제입니다 🎯\n")
    lines.append(f"이번 주 문제 수: {total}문제\n")

    for idx, p in enumerate(problems, start=1):
        problem_id = p["problemId"]
        title_ko = p.get("titleKo", "")
        url = f"https://www.acmicpc.net/problem/{problem_id}"

        # solved.ac level 정보가 있으면 난이도도 같이 표기
        level = p.get("level")
        level_str = f" (level {level})" if level is not None else ""

        lines.append(f"{idx}. {problem_id}번 - {title_ko}{level_str}\n   {url}")

    lines.append("\n즐코하세요 🔥")

    return "\n".join(lines)


def send_to_discord(content: str) -> None:
    """디스코드 웹훅으로 텍스트 메시지를 전송한다."""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url or "discord.com/api/webhooks" not in webhook_url:
        raise ValueError("DISCORD_WEBHOOK_URL 환경 변수가 올바르게 설정되지 않았습니다.")

    payload = {
        "content": content,
    }

    resp = requests.post(webhook_url, json=payload, timeout=10)
    resp.raise_for_status()


def main() -> None:
    """스크립트 진입점: 문제 선정 → 메시지 생성 → 디스코드 전송 → 사용한 문제 기록."""
    try:
        # .env 파일에서 환경 변수 로드 (있다면)
        load_env_from_file()

        used_ids = load_used_problems()

        problems = fetch_problems_with_distribution(DIFFICULTY_DISTRIBUTION, used_ids)
        if not problems:
            raise RuntimeError("문제를 한 개도 가져오지 못했습니다. 쿼리 조건을 확인해주세요.")

        message = build_discord_message(problems)
        send_to_discord(message)

        # 이번에 새로 사용한 문제들을 used_ids에 추가하고 저장
        for p in problems:
            pid = p.get("problemId")
            if pid is not None:
                used_ids.add(pid)

        save_used_problems(used_ids)
        print("디스코드로 문제 전송 및 used_problems.json 저장 완료")

    except Exception as e:
        # 크론에서 로그로 확인할 수 있도록 표준 출력에 에러 메시지 남김
        print(f"에러 발생: {e}")


if __name__ == "__main__":
    main()

