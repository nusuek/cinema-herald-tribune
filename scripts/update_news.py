import feedparser
import json
from datetime import datetime, timedelta
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

# ---- 直近7日分だけ拾う ----
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

def parse_date(entry):
    if hasattr(entry, "published"):
        try:
            return datetime(*entry.published_parsed[:6])
        except:
            return None
    return None

# ---- RSS を読む ----
for feed in FEEDS:
    print(f"Fetching: {feed['url']}")
    d = feedparser.parse(feed["url"])

    for entry in d.entries:
        pub = parse_date(entry)
        if pub is None or pub < since:
            continue

        item = {
            "title": entry.title,
            "source": feed["source"],
            "date": pub.strftime("%Y-%m-%d"),
            "url": entry.link
        }

        result[feed["section"]].append(item)

# top_storiesは3件だけ
result["top_stories"] = sorted(
    result["top_stories"],
    key=lambda x: x["date"],
    reverse=True
)[:3]

# ---- JSON に書き込む ----
OUT_PATH = "data/news.json"

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("news.json updated!")
