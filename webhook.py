import os
import requests


def _get_webhook_url() -> str:
    url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if not url:
        raise ValueError("DISCORD_WEBHOOK_URL is not set in the environment.")
    return url


def send_alert(entry: dict) -> None:
    """POST a Discord embed for a matched RSS entry."""
    url = _get_webhook_url()

    keywords_str = ", ".join(f"`{kw}`" for kw in entry["matched_keywords"])
    description = entry["summary"] or "_No summary available._"

    payload = {
        "embeds": [
            {
                "title": entry["title"] or "Untitled",
                "url": entry["link"],
                "description": description,
                "color": 0xE67E22,  # orange
                "fields": [
                    {"name": "Why it matters", "value": entry.get("ai_reason", "—"), "inline": False},
                    {"name": "Feed", "value": entry["feed_url"], "inline": False},
                ],
                "footer": {"text": "erp-signal-monitor"},
            }
        ]
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        print(f"[webhook] Alert sent: {entry['title']!r}")
    except requests.RequestException as e:
        print(f"[webhook] Failed to send alert for {entry['id']!r}: {e}")
