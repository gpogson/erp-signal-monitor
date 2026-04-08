import csv
import io
import json
import os
from datetime import datetime

import requests

FLAGGED_LOG = "flagged.json"


def load_flagged() -> list:
    if os.path.exists(FLAGGED_LOG):
        with open(FLAGGED_LOG, "r") as f:
            return json.load(f)
    return []


def append_flagged(entry: dict) -> None:
    log = load_flagged()
    log.append(entry)
    with open(FLAGGED_LOG, "w") as f:
        json.dump(log, f, indent=2)


def _get_webhook_url() -> str:
    url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if not url:
        raise ValueError("DISCORD_WEBHOOK_URL is not set.")
    return url


def send_digest(start: datetime, end: datetime, label: str) -> None:
    """Filter flagged.json between start and end, post CSV to Discord."""
    log = load_flagged()

    window = [
        e for e in log
        if start <= datetime.fromisoformat(e["flagged_at"]) < end
    ]

    print(f"[digest] {label}: {len(window)} flagged entries in window.")

    if not window:
        _post_message(f"**{label}**\nNo ERP signals flagged in this window.")
        return

    # Build CSV in memory
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Company", "URL"])
    for e in window:
        writer.writerow([e.get("company", ""), e.get("url", "")])

    csv_bytes = buf.getvalue().encode("utf-8")
    filename = f"erp_signals_{label.lower().replace(' ', '_')}.csv"

    url = _get_webhook_url()
    try:
        resp = requests.post(
            url,
            data={"content": f"**{label}** — {len(window)} ERP signal(s)"},
            files={"file": (filename, csv_bytes, "text/csv")},
            timeout=15,
        )
        resp.raise_for_status()
        print(f"[digest] Posted {label} digest to Discord.")
    except requests.RequestException as e:
        print(f"[digest] Failed to post digest: {e}")


def _post_message(content: str) -> None:
    url = _get_webhook_url()
    try:
        requests.post(url, json={"content": content}, timeout=10).raise_for_status()
    except requests.RequestException as e:
        print(f"[digest] Failed to post message: {e}")
