"""
Script 2 of 3: transform JSON.

Reads output/contacts_raw.json (from script 1), flattens HubSpot's nested JSON
into tidy rows, joins on the owner list, flags data problems, and writes:

    output/new_leads.csv       one row per contact, ready to open in Sheets/Excel
    output/lead_summary.json   counts and flags that script 3 posts to Slack

    python 02_transform_contacts.py
"""
import csv
import json
from collections import Counter
from pathlib import Path

RAW = Path("output/contacts_raw.json")
OWNERS = Path("sample_data/sample_owners.csv")
OUT_CSV = Path("output/new_leads.csv")
OUT_SUMMARY = Path("output/lead_summary.json")

FREE_EMAIL_DOMAINS = {"gmail.com", "googlemail.com", "outlook.com", "hotmail.com",
                      "yahoo.com", "icloud.com", "aol.com", "proton.me", "protonmail.com"}

# HubSpot stores internal values; people read labels.
LIFECYCLE_LABELS = {
    "subscriber": "Subscriber", "lead": "Lead", "marketingqualifiedlead": "MQL",
    "salesqualifiedlead": "SQL", "opportunity": "Opportunity", "customer": "Customer",
    "evangelist": "Evangelist", "other": "Other",
}
SOURCE_LABELS = {
    "ORGANIC_SEARCH": "Organic search", "PAID_SEARCH": "Paid search", "PAID_SOCIAL": "Paid social",
    "SOCIAL_MEDIA": "Organic social", "EMAIL_MARKETING": "Email", "REFERRALS": "Referral",
    "DIRECT_TRAFFIC": "Direct", "OFFLINE": "Offline (import, event, API)", "OTHER_CAMPAIGNS": "Other campaigns",
    "AI_REFERRALS": "AI referral",
}


def clean(value) -> str:
    """HubSpot sends missing values as null or "". Turn both into "" and trim spaces."""
    return (value or "").strip()


def load_owners(path: Path) -> dict[str, dict]:
    """owner_id -> {owner_name, team, slack_handle}. A dict makes lookups instant."""
    with path.open(newline="") as f:
        return {row["owner_id"]: row for row in csv.DictReader(f)}


def flatten(contact: dict, owners: dict[str, dict]) -> dict:
    """One nested HubSpot record -> one flat row."""
    p = contact.get("properties", {})
    email = clean(p.get("email")).lower()
    domain = email.split("@")[-1] if "@" in email else ""
    owner_id = clean(p.get("hubspot_owner_id"))
    owner = owners.get(owner_id, {})
    return {
        "hubspot_id": contact["id"],
        "email": email,
        "name": " ".join(x for x in [clean(p.get("firstname")), clean(p.get("lastname"))] if x),
        "company": clean(p.get("company")),
        "job_title": clean(p.get("jobtitle")),
        "lifecycle": LIFECYCLE_LABELS.get(clean(p.get("lifecyclestage")), clean(p.get("lifecyclestage")) or "Unknown"),
        "source": SOURCE_LABELS.get(clean(p.get("hs_analytics_source")), clean(p.get("hs_analytics_source")) or "Unknown"),
        "created": clean(p.get("createdate"))[:10],  # keep just YYYY-MM-DD
        "owner_id": owner_id,
        "owner": owner.get("owner_name", ""),
        "owner_slack": owner.get("slack_handle", ""),
        "email_domain": domain,
    }


def add_flags(rows: list[dict], owners: dict[str, dict]) -> None:
    """Add a 'flags' column listing anything a RevOps person should fix."""
    seen = Counter(r["email"] for r in rows if r["email"])
    for r in rows:
        flags = []
        if not r["owner_id"]:
            flags.append("no owner")
        elif r["owner_id"] not in owners:
            flags.append("owner not in owner list (deactivated user?)")
        if r["email_domain"] in FREE_EMAIL_DOMAINS:
            flags.append("free email domain")
        if not r["company"]:
            flags.append("missing company")
        if not r["job_title"]:
            flags.append("missing job title")
        if seen[r["email"]] > 1:
            flags.append("duplicate email")
        r["flags"] = "; ".join(flags)


def owner_label(r: dict) -> str:
    if r["owner"]:
        return r["owner"]
    return f"Unknown owner {r['owner_id']}" if r["owner_id"] else "Unassigned"


def summarise(rows: list[dict], mode: str) -> dict:
    flag_counts = Counter(f for r in rows for f in r["flags"].split("; ") if f)
    return {
        "mode": mode,
        "total": len(rows),
        "date_range": [min(r["created"] for r in rows), max(r["created"] for r in rows)] if rows else [],
        "by_lifecycle": dict(Counter(r["lifecycle"] for r in rows).most_common()),
        "by_source": dict(Counter(r["source"] for r in rows).most_common()),
        "by_owner": dict(Counter(owner_label(r) for r in rows).most_common()),
        "flag_counts": dict(flag_counts.most_common()),
        "needs_attention": [
            {"name": r["name"] or r["email"], "email": r["email"], "company": r["company"],
             "lifecycle": r["lifecycle"], "flags": r["flags"], "hubspot_id": r["hubspot_id"]}
            for r in rows if r["flags"]
        ],
    }


def main() -> None:
    if not RAW.exists():
        raise SystemExit(f"{RAW} not found. Run python 01_pull_hubspot_contacts.py first.")
    raw = json.loads(RAW.read_text())
    owners = load_owners(OWNERS)

    rows = [flatten(c, owners) for c in raw["contacts"] if not c.get("archived")]
    add_flags(rows, owners)

    OUT_CSV.parent.mkdir(exist_ok=True)
    with OUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["hubspot_id"])
        writer.writeheader()
        writer.writerows(rows)

    summary = summarise(rows, raw.get("mode", "unknown"))
    OUT_SUMMARY.write_text(json.dumps(summary, indent=2))

    print(f"Flattened {len(rows)} contacts into {OUT_CSV}")
    print(f"By lifecycle: {summary['by_lifecycle']}")
    print(f"By source:    {summary['by_source']}")
    print(f"Flags:        {summary['flag_counts']}")
    print(f"{len(summary['needs_attention'])} contacts need attention. Summary saved to {OUT_SUMMARY}")


if __name__ == "__main__":
    main()
