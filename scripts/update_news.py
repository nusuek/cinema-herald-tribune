import feedparser
import json
from datetime import datetime, timedelta
import os
import requests

# ---- RSSフィード一覧（あとで増やせる） ----
FEEDS = [
    {
        "section": "top_stories",
        "url": "https://variety.com/feed/",
        "source": "Variety"
    },
    {
        "section": "new_releases",
        "url": "http://feeds.eiga.com/eiga_news",
        "source": "映画.com"
    }
]

# 直近何日分を採用するか
DAYS = 7
now = datetime.utcnow()
since = now - timedelta(days=DAYS)

# 出力用データ
result = {
    "generated_at": now.isoformat(),
    "top_stories": [],
    "new_releases": [],
    "bd_releases": [],
    "retrospectives": [],
    "industry": [],
    "tech": [],
    "festivals": [],
    "international": [],
    "industry_affairs": []
}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 1回の実行で翻訳する最大件数（安全のため）
MAX_TRANSLATE = 40
_translate_count = 0

# 日本語ニュースのうち「芸能寄りでいらないもの」をだいたい避けるキーワード
JAPANESE_FILTER_OUT = [
    "結婚", "離婚", "交際", "熱愛", "不倫",
    "インスタ", "SNS", "X（旧Twitter）", "ツイート",
    "目撃", "私生活", "スキャンダル", "ゴシップ",
    "バラエティ", "テレビ番組", "ドラマ", "連ドラ",
    "写真集", "グラビア", "アイドル",
    "舞台挨拶", "トークイベント"
]


def is_japanese(text: str) -> bool:
    """タイトルに日本語っぽい文字が含まれているかざっくり判定"""
    for ch in text:
        code = ord(ch)
        # ひらがな・カタカナ・CJK統合漢字あたり
        if 0x3040 <= code <= 0x30ff or 0x4e00 <= code <= 0x9fff:
            return True
    return False


def should_filter_japanese_title(title: str) -> bool:
    """日本語タイトルのうち、芸能寄りなどをふるい落とす"""
    for ng in JAPANESE_FILTER_OUT:
        if ng in title:
            return True
    return False


def parse_date(entry):
    """RSSエントリから日付をいい感じに取る"""
    # 通常の published_parsed
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6])
        except Exception:
            pass

    # updated_parsed（映画.comなど）
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        try:
            return datetime(*entry.updated_parsed[:6])
        except Exception:
            pass

    # updated（ISOっぽい文字列）
    if hasattr(entry, "updated"):
        try:
            return datetime.fromisoformat(entry.updated.replace("Z", ""))
        except Exception:
            pass

    return None


def gpt_translate_title(title: str) -> str:
    """
    英語タイトルを GPT-4o mini で日本語の新聞見出しっぽく翻訳。
    ・日本語タイトルならそのまま返す
    ・APIキーがなければそのまま返す
    ・1回の実行あたり MAX_TRANSLATE 件まで
    """
    global _translate_count

    # APIキーがなければ何もしない
    if not OPENAI_API_KEY:
        return title

    # すでに上限に達していたら何もしない
    if _translate_count >= MAX_TRANSLATE:
        return title

    # もともと日本語なら翻訳不要
    if is_japanese(title):
        return title

    # シンプルに英語っぽくないものもスキップ（記号だらけなど）
    if len(title.strip()) == 0:
        return title

    try:
        _translate_count += 1

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        prompt = (
            "次の映画ニュース記事の見出しを、日本語の新聞見出しっぽく、"
            "簡潔でわかりやすい1行に翻訳してください。余計な説明は書かず、"
            "見出しのみを返してください。\n\n"
            f"{title}"
        )

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 80
        }

        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        ja = data["choices"][0]["message"]["content"].strip()
        # 念のため空なら元のタイトルを返す
        return ja or title

    except Exception as e:
        print("translate error:", e)
        return title


# ---- RSS を読む ----
for feed in FEEDS:
    print(f"Fetching: {feed['url']}")
    d = feedparser.parse(feed["url"])

    for entry in d.entries:
        pub = parse_date(entry)
        if pub is None or pub < since:
            continue

        title = entry.title.strip()
        url = entry.link

        # 映画.com など日本語ソース → 芸能寄りは落とす
        if feed["source"] == "映画.com":
            if should_filter_japanese_title(title):
                continue

        item = {
            "title": title,
            "source": feed["source"],
            "date": pub.strftime("%Y-%m-%d"),
            "url": url
        }

        result[feed["section"]].append(item)

# top_stories は新しい順に3件だけ
result["top_stories"] = sorted(
    result["top_stories"],
    key=lambda x: x["date"],
    reverse=True
)[:3]

# ---- タイトルを日本語に変換（英語だけ） ----
for section, items in result.items():
    if not isinstance(items, list):
        continue
    for item in items:
        item["title"] = gpt_translate_title(item["title"])

# ---- JSON に書き込む ----
OUT_PATH = "data/news.json"

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("news.json updated!")
