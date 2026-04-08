import ssl
import feedparser
from config import FEEDS

# Workaround for missing SSL certs on macOS Python installs
ssl._create_default_https_context = ssl._create_unverified_context


def scan_feeds(seen_ids: set) -> list[dict]:
    """
    Fetch all feeds, return all new entries (no keyword filtering).
    Each result dict has: id, title, link, summary, feed_url
    """
    entries = []

    for feed_url in FEEDS:
        try:
            feed = feedparser.parse(feed_url)
        except Exception as e:
            print(f"[scanner] Failed to fetch {feed_url}: {e}")
            continue

        for entry in feed.entries:
            entry_id = getattr(entry, "id", None) or getattr(entry, "link", None)
            if not entry_id or entry_id in seen_ids:
                continue

            title = getattr(entry, "title", "") or ""
            summary = getattr(entry, "summary", "") or ""

            entries.append({
                "id": entry_id,
                "title": title,
                "link": getattr(entry, "link", ""),
                "summary": summary[:300].strip(),
                "matched_keywords": [],
                "feed_url": feed_url,
            })

    return entries
