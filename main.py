import json
import os
import time
from datetime import datetime, timedelta

import schedule
from dotenv import load_dotenv

from config import CHECK_INTERVAL_MINUTES, SEEN_FILE
from scanner import scan_feeds
from webhook import send_alert
from ai_filter import is_erp_relevant
from digest import append_flagged, send_digest

load_dotenv()


def _load_seen() -> set:
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()


def _save_seen(seen_ids: set) -> None:
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen_ids), f, indent=2)


def run_check() -> None:
    print("[main] Running feed check...")
    seen_ids = _load_seen()

    entries = scan_feeds(seen_ids)
    print(f"[main] {len(entries)} new article(s) to evaluate.")

    sent = 0
    for entry in entries:
        relevant, company, reason = is_erp_relevant(entry)
        if relevant:
            entry["ai_reason"] = reason
            send_alert(entry)
            append_flagged({
                "company": company or entry.get("title", ""),
                "url": entry.get("link", ""),
                "title": entry.get("title", ""),
                "reason": reason,
                "flagged_at": datetime.now().isoformat(),
            })
            print(f"[main] Sent: {entry['title']!r} — {reason}")
            sent += 1
        else:
            print(f"[main] Skipped: {entry['title']!r} — {reason}")
        seen_ids.add(entry["id"])

    _save_seen(seen_ids)
    print(f"[main] Done. {sent} alert(s) sent.")


def morning_digest() -> None:
    """8am digest: everything flagged since 3:30pm the previous day."""
    now = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    start = (now - timedelta(days=1)).replace(hour=15, minute=30, second=0)
    end = now
    send_digest(start, end, "Morning Digest (3:30pm–8:00am)")


def eod_digest() -> None:
    """3:30pm digest: everything flagged since 8am today."""
    now = datetime.now().replace(hour=15, minute=30, second=0, microsecond=0)
    start = now.replace(hour=8, minute=0, second=0)
    end = now
    send_digest(start, end, "End-of-Day Digest (8:00am–3:30pm)")


def main() -> None:
    print(f"[main] erp-signal-monitor starting. Checking every {CHECK_INTERVAL_MINUTES} minutes.")
    run_check()

    schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(run_check)
    schedule.every().day.at("08:00").do(morning_digest)
    schedule.every().day.at("15:30").do(eod_digest)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
