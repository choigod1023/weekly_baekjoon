# Baekjoon Weekly Problem Notifier

[한국어](README.md) · **日本語** · [English](README.en.md)

> solved.ac API で難易度別に Baekjoon の問題を抽出し、**Discord Webhook（@everyone）** で定期的に送る Python スクリプトです。

## 紹介

`baekjoon_weekly.py` 一つで動く単一ファイルのスクリプトです。実行すると [solved.ac](https://solved.ac) の問題検索 API（`/api/v3/search/problem`）から難易度区間ごとに問題をランダムに選び、まだ送っていない問題だけを [Baekjoon (acmicpc.net)](https://www.acmicpc.net) の問題リンクと共に Discord チャンネルへ送信します。勉強会・サークルのチャンネルに毎週「今週のアルゴリズム問題」を自動投稿する用途で作りました。

1 回の実行 = 1 回の送信という構造で、週 1 回のような定期実行は cron（Linux）などの外部スケジューラに任せます。

## ✨ 主な機能

- **難易度区間ごとのランダム選定**: solved.ac の tier 値を基準に `easy`（tier 1〜8）と `hard`（tier 9〜15）の 2 区間から問題を選びます。デフォルトの配分は `easy` 1 問 + `hard` 1 問の計 2 問です（`DIFFICULTY_DISTRIBUTION` で調整可能）。
- **人気問題を優先**: `acceptedUserCount` が `MIN_ACCEPTED_USER_COUNT`（デフォルト 1000）以上の「よく解かれている問題」を優先し、足りない場合は条件を段階的に緩めるフォールバックがあります。
- **韓国語問題のフィルタ**: `ONLY_KOREAN_PROBLEMS = True` の場合、`titleKo`（韓国語タイトル）がある問題のみを選びます。
- **重複防止**: 送信済みの問題 ID を `used_problems.json` に保存し、次回の実行でできるだけ重複しないよう除外します。
- **Discord Webhook 送信**: `@everyone` メンションと共に、問題番号・韓国語タイトル・solved.ac の level・Baekjoon の問題 URL を整理して送信します。
- **環境変数によるシークレット管理**: Webhook URL はコードに書かず、`.env` ファイルまたは環境変数（`DISCORD_WEBHOOK_URL`）から読み込みます。

## 🛠 技術スタック

- **Python 3.9+**（`set[int]`, `list[dict]` など標準のジェネリック型ヒントを使用）
- **requests** — solved.ac API の呼び出しと Discord Webhook への POST
- **solved.ac API v3** — 問題データのソース
- **Discord Webhook** — メッセージの送信先

外部依存は `requests` のみで、`.env` のパースはライブラリを使わず自前で実装しています。

## 🏗 動作の流れ

1. `.env` ファイルがあれば読み込み、`os.environ` に反映します。
2. `used_problems.json` から、以前送った問題 ID の集合を読み込みます。
3. `DIFFICULTY_DISTRIBUTION` の各区間について solved.ac 検索 API を呼び出します。
   - クエリ: `tier:{min}..{max}`, `sort=random`, `size=50`
   - 韓国語問題 → 人気問題 → 未使用問題 の順にフィルタし、必要な数だけサンプリング
4. 選定した問題から Discord メッセージ文字列を作り、`DISCORD_WEBHOOK_URL` へ POST します。
5. 今回送った問題 ID を `used_problems.json` に追記保存します。

スケジュール／トリガーはコードに内蔵していません。スクリプトは 1 回実行型で、定期実行は cron などで構成します（下記参照）。

### 設定値（`baekjoon_weekly.py` の冒頭）

```python
ONLY_KOREAN_PROBLEMS = True          # titleKo がある韓国語問題のみ使用
MIN_ACCEPTED_USER_COUNT = 1000       # 「よく解かれている問題」の基準となる AC ユーザー数
DIFFICULTY_DISTRIBUTION = {
    "easy": 1,   # tier 1~8 から 1 問
    "hard": 1,   # tier 9~15 から 1 問
}
TIER_RANGES = {
    "easy": (1, 8),
    "hard": (9, 15),
}
```

`DIFFICULTY_DISTRIBUTION` の値を増やせば（例: `easy` 2, `hard` 2）、一度により多くの問題を送れます。

## 🚀 はじめかた

### 1. 必要条件とインストール

- Python 3.9 以上

```bash
pip install requests
```

### 2. 環境変数の設定

プロジェクトルートに `.env` ファイルを作り、Discord Webhook URL を入れます。コードが実際に参照する変数は次の 1 つだけです。

```bash
# .env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxxxxxx/yyyyyyyy
```

`.env` の代わりにシェルの環境変数として `DISCORD_WEBHOOK_URL` を直接指定しても構いません。`.env` ファイルは Git にコミットしないことを推奨します。

### 3. 実行

```bash
python baekjoon_weekly.py
```

成功すると `@everyone 이번 주 백준 알고리즘 문제입니다 🎯` というメッセージと共に選定された問題が Discord チャンネルへ送信され、`used_problems.json` が更新されます。

### 4. cron による定期実行（Linux サーバーの例）

```bash
# 毎週月曜 09:00 に実行
0 9 * * 1 /usr/bin/python3 /path/to/weekly_baekjoon/baekjoon_weekly.py >> /path/to/weekly_baekjoon/cron.log 2>&1
```

パスは実際のデプロイ先に置き換えてください。サーバー側でも `.env`（または環境変数）を同様に設定する必要があります。

## 📁 ファイル構成

```
weekly_baekjoon/
├── baekjoon_weekly.py   # メインスクリプト（問題選定 → メッセージ生成 → 送信 → 記録）
├── used_problems.json   # 送信済み問題 ID の保存（実行時に自動生成／更新）
├── .env                 # DISCORD_WEBHOOK_URL（自分で作成）
└── README.md
```

---

## 👤 コントリビューションと開発環境

| 項目 | 内容 |
|---|---|
| **貢献比率** | **100%**（単独開発） |
| **コミット** | 7 / 7（本人 / 全人力コミット） |
| **参加人数** | 1 名 |

<sub>集計基準: origin の **すべてのブランチ** から到達可能なコミット（マージコミット・空コミットは除外）を対象とし、コミットの author メールアドレス基準で、同一人物の複数のメールアドレスは合算、ボット・自動化コミットは除外しています。</sub>
