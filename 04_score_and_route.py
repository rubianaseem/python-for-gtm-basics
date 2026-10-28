"""
Script 4 of 4: score, route, and write CRM-ready outputs.

Reads output/new_leads.csv + sample_data/routing_rules.json, scores each lead,
assigns a route (ae_review / sdr_sequence / nurture / quarantine), and writes:

    output/scored_leads.csv          full scored table
    output/crm_ready_import.csv      rows safe to import / update (no quarantine)
    output/review_queue.csv          bad / ambiguous rows for a human
    output/routing_summary.json      counts for the Slack digest

Judgment this teaches:
  - Retries belong in the pull step; routing must not trust a half-fetched page.
  - Flags are cheap insurance; a review queue beats silent bad CRM writes.
  - Quarantine disposable / invalid emails before an SDR sequence burns them.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

LEADS = Path("output/new_leads.csv")
OWNERS = Path("sample_data/sample_owners.csv")
RULES = Path("sample_data/routing_rules.json")
OUT_SCORED = Path("output/scored_leads.csv")
OUT_CRM = Path("output/crm_ready_import.csv")
OUT_REVIEW = Path("output/review_queue.csv")
OUT_SUMMARY = Path("output/routing_summary.json")


def load_rules() -> dict:
    return json.loads(RULES.read_text())


def load_owners() -> list[dict]:
    with OWNERS.open(newline="") as f:
        return list(csv.DictReader(f))


def score_row(r: dict, rules: dict) -> tuple[int, list[str]]:
    w = rules["score_weights"]
    reasons = []
    score = 0
    flags = set(f.strip() for f in (r.get("flags") or "").split(";") if f.strip())

    if "invalid email" in flags or "disposable email" in flags:
        return 0, ["quarantine: bad or disposable email"]

    domain = (r.get("email_domain") or "").lower()
    free = domain in {"gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "yahoo.com", "icloud.com"}
    if r.get("email") and not free:
        score += w.get("business_email", 0)
        reasons.append("business email")

    if r.get("country") in rules.get("icp_countries", []):
        score += w.get("icp_country", 0)
        reasons.append("ICP country")

    title = (r.get("job_title") or "").lower()
    if any(k in title for k in rules.get("icp_titles_keywords", [])):
        score += w.get("icp_title", 0)
        reasons.append("ICP title")

    if r.get("company"):
        score += w.get("has_company", 0)
        reasons.append("has company")

    if r.get("phone") and "invalid phone" not in flags:
        score += w.get("has_phone", 0)
        reasons.append("has phone")

    if r.get("lifecycle") in {"MQL", "SQL", "Opportunity", "Customer"}:
        score += w.get("mql_or_later", 0)
        reasons.append(f"lifecycle {r.get('lifecycle')}")

    if r.get("source") in {"Paid search", "Paid social", "Referral"}:
        score += w.get("paid_or_referral_source", 0)
        reasons.append(f"source {r.get('source')}")

    if r.get("owner"):
        score += w.get("has_owner", 0)
        reasons.append("has owner")

    return score, reasons


def pick_route(score: int, r: dict, rules: dict) -> str:
    flags = set(f.strip() for f in (r.get("flags") or "").split(";") if f.strip())
    if "invalid email" in flags or "disposable email" in flags:
        return "quarantine"
    if "duplicate email" in flags or "owner not in owner list (deactivated user?)" in flags:
        return "review"
    th = rules["route_thresholds"]
    if score >= th["ae_review"]:
        return "ae_review"
    if score >= th["sdr_sequence"]:
        return "sdr_sequence"
    if score >= th["nurture"]:
        return "nurture"
    return "review"


def suggest_owner(r: dict, route: str, owners: list[dict], rules: dict) -> str:
    if r.get("owner") and route != "quarantine":
        return r["owner"]
    team = rules.get("sdr_team") if route == "sdr_sequence" else rules.get("midmarket_owner_team")
    if route == "ae_review":
        # Prefer enterprise for high score MQLs with director+ titles
        title = (r.get("job_title") or "").lower()
        if any(k in title for k in ("vp", "head of", "director", "chief")):
            team = rules.get("enterprise_owner_team")
    for o in owners:
        if o.get("team") == team:
            return o["owner_name"]
    return ""


def main() -> None:
    if not LEADS.exists():
        raise SystemExit(f"{LEADS} not found. Run python 02_transform_contacts.py first.")
    rules = load_rules()
    owners = load_owners()
    with LEADS.open(newline="") as f:
        rows = list(csv.DictReader(f))

    scored = []
    for r in rows:
        score, reasons = score_row(r, rules)
        route = pick_route(score, r, rules)
        suggested = suggest_owner(r, route, owners, rules)
        scored.append({
            **r,
            "fit_score": score,
            "score_reasons": "; ".join(reasons),
            "route": route,
            "suggested_owner": suggested,
        })

    OUT_SCORED.parent.mkdir(exist_ok=True)
    with OUT_SCORED.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(scored[0].keys()) if scored else ["hubspot_id"])
        w.writeheader()
        w.writerows(scored)

    crm_rows = [r for r in scored if r["route"] in {"ae_review", "sdr_sequence", "nurture"}]
    with OUT_CRM.open("w", newline="") as f:
        fields = ["hubspot_id", "email", "name", "company", "job_title", "lifecycle",
                  "fit_score", "route", "suggested_owner", "owner", "country"]
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(crm_rows)

    review_rows = [r for r in scored if r["route"] in {"review", "quarantine"} or r.get("flags")]
    with OUT_REVIEW.open("w", newline="") as f:
        fields = ["hubspot_id", "email", "name", "company", "route", "fit_score", "flags",
                  "score_reasons", "suggested_owner", "owner"]
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(review_rows)

    summary = {
        "total": len(scored),
        "by_route": dict(Counter(r["route"] for r in scored).most_common()),
        "avg_score": round(sum(r["fit_score"] for r in scored) / len(scored), 1) if scored else 0,
        "crm_ready": len(crm_rows),
        "review_queue": len(review_rows),
        "top_ae_review": [
            {"name": r["name"] or r["email"], "score": r["fit_score"], "owner": r["suggested_owner"]}
            for r in sorted([x for x in scored if x["route"] == "ae_review"], key=lambda x: -x["fit_score"])[:5]
        ],
    }
    OUT_SUMMARY.write_text(json.dumps(summary, indent=2))

    print(f"Scored {len(scored)} leads -> {OUT_SCORED}")
    print(f"By route: {summary['by_route']} (avg score {summary['avg_score']})")
    print(f"CRM-ready rows: {len(crm_rows)} -> {OUT_CRM}")
    print(f"Review queue:   {len(review_rows)} -> {OUT_REVIEW}")
    print("Nothing was written to HubSpot. Import crm_ready_import.csv only after a human glance.")


if __name__ == "__main__":
    main()
