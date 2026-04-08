import os
import requests

# System prompt — edit this to refine what counts as ERP-relevant
ERP_PROMPT = """You are a signal filter for a business development professional who sells ERP software and financial systems.

Your job is to read a news article and decide if it represents a buying signal — meaning the company or person mentioned may be in the market for ERP, accounting, or financial operations software.

Flag the article as relevant if it mentions ANY of the following signals:

GROWTH & CHANGE SIGNALS:
- Digital transformation initiatives or announcements
- Operational scaling, headcount growth, or business expansion
- New facilities, warehouses, offices, or geographic expansion
- Mergers, acquisitions, or divestitures (M&A activity)
- New funding rounds (seed, Series A/B/C, PE investment, IPO)

LEADERSHIP SIGNALS:
- New executive hires: CIO, CTO, COO, CFO, Controller, VP Finance, VP Operations, or similar roles
- C-suite restructuring or leadership transitions

TECHNOLOGY SIGNALS:
- Technology modernization or legacy system replacement
- Supply chain changes, new logistics infrastructure, or fulfillment operations
- Any mention of ERP software (evaluating, replacing, implementing, or struggling with)

ERP VENDOR SIGNALS (always flag if any of these are mentioned):
- NetSuite, SAP, Oracle, Microsoft Dynamics, Sage, Epicor, Acumatica, Infor, Workday, QuickBooks Enterprise
- Any ERP vendor by name, or comparison of ERP systems

Respond with ONLY a JSON object in this exact format:
{"relevant": true, "company": "Exact Company Name", "reason": "one sentence explanation of which signal was detected"}
or
{"relevant": false, "company": "", "reason": "one sentence explanation of why it was not relevant"}

For "company", extract the primary company name from the article. If multiple companies are mentioned, use the one the article is primarily about.

Do not include any other text."""


def is_erp_relevant(entry: dict) -> tuple[bool, str]:
    """
    Send article to AI API and return (is_relevant, reason).
    Configure AI_API_URL and AI_API_KEY in .env to plug in any model.
    """
    api_url = os.getenv("AI_API_URL", "").strip()
    api_key = os.getenv("AI_API_KEY", "").strip()
    if not api_url or not api_key:
        print("[ai_filter] AI_API_URL or AI_API_KEY not set — skipping AI filter, passing all articles.")
        return True, "", "AI filter not configured"

    article_text = f"Title: {entry['title']}\n\nSummary: {entry['summary']}"

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": ERP_PROMPT},
            {"role": "user", "content": article_text},
        ],
        "max_tokens": 100,
        "temperature": 0,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(api_url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        # Parse the model's JSON response out of the message content
        import json
        content = data["choices"][0]["message"]["content"].strip()
        result = json.loads(content)
        return result["relevant"], result.get("company", ""), result["reason"]

    except Exception as e:
        print(f"[ai_filter] Error calling AI API: {e} — passing article through.")
        return True, "", "AI filter error — passed through"
