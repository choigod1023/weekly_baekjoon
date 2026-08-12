# Baekjoon Weekly Problem Notifier

[한국어](README.md) · [日本語](README.ja.md) · **English**

> A Python script that picks Baekjoon problems by difficulty via the solved.ac API and posts them periodically to a **Discord webhook (@everyone)**.

## About

A single-file script that runs entirely from `baekjoon_weekly.py`. On each run it queries the [solved.ac](https://solved.ac) problem search API (`/api/v3/search/problem`), picks problems at random within difficulty bands, filters out ones already sent, and posts them to a Discord channel with links to [Baekjoon (acmicpc.net)](https://www.acmicpc.net). I built it to auto-post "this week's algorithm problems" to a study-group or club channel.

One run = one post; recurring weekly execution is delegated to an external scheduler such as cron on Linux.

## ✨ Features

- **Random selection per difficulty band**: uses solved.ac tier values to draw from `easy` (tier 1–8) and `hard` (tier 9–15). The default distribution is 1 easy + 1 hard, i.e. 2 problems per run (configurable via `DIFFICULTY_DISTRIBUTION`).
- **Prefers popular problems**: prioritizes "widely solved" problems whose `acceptedUserCount` is at least `MIN_ACCEPTED_USER_COUNT` (default 1000), with fallback logic that progressively relaxes the constraint if there aren't enough.
- **Korean-problem filter**: with `ONLY_KOREAN_PROBLEMS = True`, only problems that have a `titleKo` (Korean title) are selected.
- **Deduplication**: already-sent problem IDs are stored in `used_problems.json` and excluded from later runs as far as possible.
- **Discord webhook delivery**: posts an `@everyone` mention along with problem number, Korean title, solved.ac level, and the Baekjoon problem URL.
- **Secrets via environment variables**: the webhook URL is never in code — it's read from a `.env` file or the `DISCORD_WEBHOOK_URL` environment variable.

## 🛠 Tech stack

- **Python 3.9+** (uses standard generic type hints such as `set[int]`, `list[dict]`)
- **requests** — solved.ac API calls and the Discord webhook POST
- **solved.ac API v3** — the problem data source
- **Discord Webhook** — the delivery target

The only external dependency is `requests`; `.env` parsing is implemented by hand without an extra library.

## 🏗 How it works

1. If a `.env` file exists, it is read and applied to `os.environ`.
2. The set of previously sent problem IDs is loaded from `used_problems.json`.
3. For each band in `DIFFICULTY_DISTRIBUTION`, the solved.ac search API is called.
   - Query: `tier:{min}..{max}`, `sort=random`, `size=50`
   - Filter by Korean → popular → unused, then sample as many as needed
4. A Discord message string is built from the selected problems and POSTed to `DISCORD_WEBHOOK_URL`.
5. The IDs sent this run are appended to `used_problems.json`.

Scheduling/triggering is not built into the code. The script is single-shot; set up recurring runs with cron or similar (see below).

### Configuration (top of `baekjoon_weekly.py`)

```python
ONLY_KOREAN_PROBLEMS = True          # only use Korean problems (those with titleKo)
MIN_ACCEPTED_USER_COUNT = 1000       # AC-user threshold defining a "widely solved" problem
DIFFICULTY_DISTRIBUTION = {
    "easy": 1,   # 1 problem from tier 1~8
    "hard": 1,   # 1 problem from tier 9~15
}
TIER_RANGES = {
    "easy": (1, 8),
    "hard": (9, 15),
}
```

Raise the values in `DIFFICULTY_DISTRIBUTION` (e.g. `easy` 2, `hard` 2) to send more problems per run.

## 🚀 Getting started

### 1. Requirements and installation

- Python 3.9 or newer

```bash
pip install requests
```

### 2. Environment variables

Create a `.env` file in the project root with your Discord webhook URL. The code reads exactly one variable:

```bash
# .env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxxxxxx/yyyyyyyy
```

You can also set `DISCORD_WEBHOOK_URL` directly as a shell environment variable instead of using `.env`. Keeping `.env` out of Git is recommended.

### 3. Run

```bash
python baekjoon_weekly.py
```

On success the selected problems are posted to the Discord channel with the message `@everyone 이번 주 백준 알고리즘 문제입니다 🎯`, and `used_problems.json` is updated.

### 4. Recurring runs with cron (Linux server example)

```bash
# Run every Monday at 09:00
0 9 * * 1 /usr/bin/python3 /path/to/weekly_baekjoon/baekjoon_weekly.py >> /path/to/weekly_baekjoon/cron.log 2>&1
```

Replace the paths with your actual deployment location. The server needs the same `.env` (or environment variable) configuration.

## 📁 File layout

```
weekly_baekjoon/
├── baekjoon_weekly.py   # main script (select → build message → send → record)
├── used_problems.json   # already-sent problem IDs (created/updated automatically)
├── .env                 # DISCORD_WEBHOOK_URL (create it yourself)
└── README.md
```

---

## 👤 Contribution & development environment

| Item | Detail |
|---|---|
| **Contribution share** | **100%** (solo development) |
| **Commits** | 7 / 7 (mine / all human commits) |
| **Contributors** | 1 |

<sub>Counting basis: commits reachable from **every branch** on origin (merge commits and empty commits excluded), counted by commit author email with one person’s multiple addresses merged; bot and automation commits are excluded.</sub>
