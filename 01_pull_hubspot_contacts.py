"""
Script 1 of 3: call the HubSpot API.

Pulls every contact created in the last N days from HubSpot's CRM search API,
following pagination, and saves the raw JSON to output/contacts_raw.json.

No HubSpot token? It runs in mock mode and reads the two sample "API pages" in
sample_data/, so you can see exactly what the real API sends back.

    python 01_pull_hubspot_contacts.py            # last 7 days
    python 01_pull_hubspot_contacts.py --days 14  # last 14 days
"""
import argparse
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

try:  # optional: read .env if python-dotenv is installed
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SEARCH_URL = "https://api.hubapi.com/crm/v3/objects/contacts/search"
PROPERTIES = [
    "email", "firstname", "lastname", "company", "jobtitle",
    "lifecyclestage", "hs_analytics_source", "hubspot_owner_id", "createdate",
]
SAMPLE_PAGES = [Path("sample_data/hubspot_contacts_page1.json"),
                Path("sample_data/hubspot_contacts_page2.json")]
OUTPUT = Path("output/contacts_raw.json")


def build_search_body(days: int, after: str | None) -> dict:
    """The JSON body HubSpot's search endpoint expects."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    since_ms = int(since.timestamp() * 1000)  # HubSpot compares dates as epoch milliseconds
    body = {
        "filterGroups": [{
            "filters": [{"propertyName": "createdate", "operator": "GTE", "value": str(since_ms)}]
        }],
        "properties": PROPERTIES,
        "sorts": [{"propertyName": "createdate", "direction": "ASCENDING"}],
        "limit": 100,  # the most the search API returns per page
    }
    if after:
        body["after"] = after
    return body


def post_with_retry(url: str, headers: dict, body: dict, attempts: int = 4) -> dict:
    """POST, and if HubSpot says 'slow down' (429) or has a blip (5xx), wait and try again."""
    for attempt in range(1, attempts + 1):
        resp = requests.post(url, headers=headers, json=body, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code in (429, 500, 502, 503, 504) and attempt < attempts:
            wait = int(resp.headers.get("Retry-After", 2 ** attempt))
            print(f"  HubSpot returned {resp.status_code}, waiting {wait}s and retrying ({attempt}/{attempts})")
            time.sleep(wait)
            continue
        if resp.status_code == 401:
            raise SystemExit("HubSpot said 401 Unauthorized: check HUBSPOT_TOKEN is a valid private app token.")
        if resp.status_code == 403:
            raise SystemExit("HubSpot said 403 Forbidden: give the private app the crm.objects.contacts.read scope.")
        raise SystemExit(f"HubSpot error {resp.status_code}: {resp.text[:300]}")
    raise SystemExit("Gave up after several retries.")


def fetch_live(token: str, days: int) -> list[dict]:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    contacts, after, page = [], None, 0
    while True:
        page += 1
        data = post_with_retry(SEARCH_URL, headers, build_search_body(days, after))
        contacts.extend(data.get("results", []))
        print(f"  page {page}: {len(data.get('results', []))} contacts (total so far {len(contacts)})")
        after = data.get("paging", {}).get("next", {}).get("after")
        if not after:
            return contacts
        if len(contacts) >= 10_000:  # the search API stops paging at 10,000 results
            print("  Hit HubSpot's 10,000-result search limit; narrow --days to get the rest.")
            return contacts


def fetch_mock() -> list[dict]:
    """Same loop as fetch_live, but each 'page' comes from a file instead of the internet."""
    contacts = []
    for page, path in enumerate(SAMPLE_PAGES, start=1):
        data = json.loads(path.read_text())
        contacts.extend(data["results"])
        has_next = "next" in data.get("paging", {})
        print(f"  page {page}: {len(data['results'])} contacts (total so far {len(contacts)}), "
              f"{'more pages to fetch' if has_next else 'last page'}")
    return contacts


def main() -> None:
    parser = argparse.ArgumentParser(description="Pull recent HubSpot contacts to JSON.")
    parser.add_argument("--days", type=int, default=7, help="look back this many days (default 7)")
    args = parser.parse_args()

    token = os.environ.get("HUBSPOT_TOKEN", "").strip()
    if token:
        print(f"Calling HubSpot for contacts created in the last {args.days} days…")
        contacts = fetch_live(token, args.days)
        mode = "live"
    else:
        print("No HUBSPOT_TOKEN set, so using the sample API pages in sample_data/ (mock mode).")
        contacts = fetch_mock()
        mode = "mock"

    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps({"mode": mode, "pulled_at": datetime.now(timezone.utc).isoformat(),
                                  "contacts": contacts}, indent=2))
    print(f"Saved {len(contacts)} contacts to {OUTPUT}")


if __name__ == "__main__":
    main()
