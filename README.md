# Python for GTM: Basics (pull -> transform -> score/route -> Slack)

**A cohesive offline-first GTM pipeline in Python: pull HubSpot contacts (with pagination and polite retries), flatten and flag messy rows, score and route leads, then post a Slack digest — with a review queue so bad data never silently hits the CRM.**

> Built by Rubia Naseem, GTM Engineer (12+ yrs CRM/RevOps, HubSpot & Salesforce).

---

## The pain point

HubSpot workflows cover a lot until you need data "out and in" with judgment: retries on 429s, owner joins, quarantine for disposable emails, and a human review queue before import.

- *"I'm in RevOps and have two weeks time and want to learn the basics of working with the Hubspot API. Just getting data out and in from Gong, Zoominfo and so on…"* ([r/hubspot: Looking for an API course](https://www.reddit.com/r/hubspot/comments/1mczh0n/looking_for_an_api_course/))
- *"Struggling with HubSpot API: Extracting Large Dataset & ETL Pipeline"* — pagination, batch reads, and rate limits are the usual blockers once you leave the UI. ([r/hubspot: Struggling with HubSpot API](https://www.reddit.com/r/hubspot/comments/1bozbwx/struggling_with_hubspot_api_extracting_large/))

---

## What it does

- **Pull:** HubSpot CRM search with cursor pagination and retry-on-429; sample API pages stand in when no token is set
- **Transform:** flatten nested properties, join owners, flag invalid/disposable/free emails, missing fields, duplicate emails, bad phones, unknown owners
- **Score and route:** fit score from ICP rules -> `ae_review` / `sdr_sequence` / `nurture` / `review` / `quarantine`
- **Outputs:** `scored_leads.csv`, CRM-ready import CSV, review queue CSV, Slack digest (dry-run without a webhook)
- **Optional Claude** for the Slack headline only
- **Read-only toward HubSpot:** nothing writes to the CRM

---

## Where each step runs

1. **GitHub** holds the code. Clone or download the ZIP.
2. **Terminal** runs `python pipeline.py` (or the four scripts one by one).
3. **HubSpot** is read-only via token, or mocked from `sample_data/`.
4. **You** clear `output/review_queue.csv` before importing `crm_ready_import.csv`.
5. **Slack** gets the digest when `SLACK_WEBHOOK_URL` is set; otherwise a dry-run payload is printed.

---

## Quick start

```bash
git clone https://github.com/rubianaseem/python-for-gtm-basics.git
cd python-for-gtm-basics
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python pipeline.py   # sample data, no keys needed
```

Outputs land in `output/` (gitignored).

---

## Example output

```text
=== 01_pull_hubspot_contacts.py ===
No HUBSPOT_TOKEN set, so using the sample API pages in sample_data/ (mock mode).
Saved 12 contacts to output/contacts_raw.json

=== 04_score_and_route.py ===
By route: {'ae_review': ..., 'review': ..., 'quarantine': ...}
CRM-ready rows: N -> output/crm_ready_import.csv
Review queue:   M -> output/review_queue.csv
```

---

## Scripts in the pipeline

| Script | Job |
| --- | --- |
| `01_pull_hubspot_contacts.py` | Paginated HubSpot search + 429 retries (or mock pages) |
| `02_transform_contacts.py` | Flatten, owner join, data-quality flags |
| `04_score_and_route.py` | Fit score, route, CRM-ready + review queue |
| `03_post_slack_digest.py` | Block Kit digest (dry-run without webhook) |
| `pipeline.py` / `run_all.py` | Run all four in order |

## What you are supposed to learn

Not "how to print Hello HubSpot." The judgment calls: follow every search page, retry on 429, flag instead of silently dropping rows, quarantine disposable emails, and keep a review queue between automation and CRM import. Edit `sample_data/routing_rules.json` before you trust scores on your own data.

## More

- [SETUP.md](SETUP.md): tokens, owner list, routing_rules.json, scheduling, troubleshooting
- [docs/WALKTHROUGH.md](docs/WALKTHROUGH.md): why retries, flags, and a review queue exist
- [docs/DETAILS.md](docs/DETAILS.md): quotes, output files, cost, stack swap
