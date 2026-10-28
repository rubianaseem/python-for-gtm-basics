# Details: Python for GTM: Basics

Everything that used to sit in the main README, kept here so the README stays short. Back to the [README](../README.md).

## Background

Most of my GTM automation lives in no-code tools, and that's fine until a job needs something they can't do cleanly: a custom join, a bit of logic that's ten nodes in n8n and five lines in Python, or a quick script to check what an API actually sends back. So item 2 on my GTM Engineer skills roadmap is getting properly comfortable with the basics: `requests`, JSON, and calling APIs.

Instead of toy examples, the three scripts here build one real thing together: a **weekly new-lead digest**. Script 1 pulls the contacts created in the last 7 days from HubSpot, script 2 flattens them into a CSV and flags what needs fixing (no owner, an owner who's left, free email domains, duplicates, missing company or title), and script 3 posts a short summary to a Slack channel. Each one is small enough to read top to bottom, and each runs on sample data with no keys at all.

## Where each step runs (full version)

If you can create a repo but aren't sure where you actually *run* this, here's the whole flow in order:

1. **GitHub** is where the code lives. Copy it to your laptop with `git clone https://github.com/rubianaseem/python-for-gtm-basics.git`, or click **Code → Download ZIP**.
2. **Terminal** (Mac Terminal, or the terminal inside Cursor) is where you run the scripts, one after another: `python 01_pull_hubspot_contacts.py`, then `python 02_transform_contacts.py`, then `python 03_post_slack_digest.py`. Or run all three with `python run_all.py`.
3. **HubSpot** is only read. With no token, script 1 uses two sample "API pages" in `sample_data/`. With a private app token in `.env`, it calls HubSpot's search API for real. **Nothing here ever writes to HubSpot.**
4. **Claude is optional.** With no key, script 3 builds the Slack headline from a built-in template. With an Anthropic key in `.env`, Claude writes the headline from the same numbers. It still runs in the terminal; you don't open the Claude app.
5. **Slack** is the last step. With no webhook, script 3 does a dry run: it prints the exact message and saves it to `output/slack_payload.json`. With a webhook URL in `.env`, it posts to that channel.
6. **You, afterwards.** Open `output/new_leads.csv`, fix the flagged records in HubSpot by hand (assign owners, merge duplicates), and that's the loop.

## Full feature list

- **Script 1, call an API:** `requests.post` to HubSpot's CRM search endpoint with a date filter, follows `paging.next.after` until the last page, retries on `429` rate limits and `5xx` blips using `Retry-After`, and gives a plain-English message for `401` and `403`
- **Script 2, transform JSON:** flattens HubSpot's nested `properties` into flat rows, turns `null` and `""` into one "missing" value, swaps internal values (`marketingqualifiedlead`, `PAID_SOCIAL`) for labels people read, joins each contact to an owner list from a CSV, and writes `new_leads.csv` plus a `lead_summary.json`
- **Data-quality flags:** no owner, owner ID not in the owner list (often a deactivated user), free email domain, missing company, missing job title, and duplicate emails (case-insensitive)
- **Script 3, post to Slack:** builds a Block Kit message (header, headline, lifecycle and owner counts, the records that need attention, with links to HubSpot if you set your Hub ID) and posts it with an incoming webhook, checking Slack's `ok` reply
- **Mock mode everywhere:** no HubSpot token, no Slack webhook and no Anthropic key needed to see the whole thing run
- **Claude as an upgrade, not a dependency:** if the API call fails for any reason, it falls back to the template and says so

## The pain point: all quotes and sources

This one comes from my own roadmap rather than a broken process, but it's the same gap I see RevOps people talk about. You can do a lot in HubSpot without code, and the moment you want data "out and in" between tools, the docs assume you already know how APIs work:

- *"I’m in RevOps and have two weeks time and want to learn the basics of working with the Hubspot API. Just getting data out and in from Gong, Zoominfo and so on…"* and *"the api doc is too technical for me at the moment."* ([r/hubspot: Looking for an API course](https://www.reddit.com/r/hubspot/comments/1mczh0n/looking_for_an_api_course/))
- A reply in the same thread lists what bites in production: *"Rate limits hit hard at scale"*, *"Error handling gets complex"* and *"One bad sync can corrupt thousands of records."* (Worth knowing: that reply was written by the founder of a sync tool, as they say in the post.)
- On the HubSpot Community, the answer to "what languages should I learn" is less about the language and more about this: *"you’ll be working with HTTP methods (GET, POST, PUT, DELETE) and JSON data structures."* ([HubSpot Community: what are the programming languages I should learn to develop within hubspot?](https://community.hubspot.com/t/what-are-the-programming-languages-i-should-learn-to-develop-within-hubspot/123294/5))

So the scripts here cover exactly those pieces: a real request, real pagination, rate-limit retries, a JSON reshape, and a webhook post, with nothing that writes back to the CRM.

## Quick start and output files

```bash
git clone https://github.com/rubianaseem/python-for-gtm-basics.git
cd python-for-gtm-basics
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run all three on the sample data (no keys needed)
python run_all.py

# Or one at a time
python 01_pull_hubspot_contacts.py
python 02_transform_contacts.py
python 03_post_slack_digest.py
```

Everything the scripts write goes into `output/` (ignored by Git, so contact data never gets committed).

| File | Written by | What's in it |
|---|---|---|
| `output/contacts_raw.json` | script 1 | Exactly what HubSpot returned, all pages joined |
| `output/new_leads.csv` | script 2 | One flat row per contact, with owner names and a `flags` column |
| `output/lead_summary.json` | script 2 | Counts by lifecycle, source and owner, plus the flagged records |
| `output/slack_payload.json` | script 3 | The Slack message as JSON (paste it into Slack's Block Kit Builder to preview it) |

## Full example output

From `python run_all.py` on the sample data, with no keys set:

```text
=== 01_pull_hubspot_contacts.py ===
No HUBSPOT_TOKEN set, so using the sample API pages in sample_data/ (mock mode).
  page 1: 4 contacts (total so far 4), more pages to fetch
  page 2: 3 contacts (total so far 7), last page
Saved 7 contacts to output/contacts_raw.json

=== 02_transform_contacts.py ===
Flattened 7 contacts into output/new_leads.csv
By lifecycle: {'MQL': 2, 'Lead': 2, 'SQL': 1, 'Opportunity': 1, 'Subscriber': 1}
By source:    {'Organic search': 1, 'Paid social': 1, 'Paid search': 1, 'Referral': 1, 'Offline (import, event, API)': 1, 'Direct': 1, 'Email': 1}
Flags:        {'duplicate email': 2, 'no owner': 2, 'free email domain': 2, 'missing company': 2, 'missing job title': 2, 'owner not in owner list (deactivated user?)': 1}
5 contacts need attention. Summary saved to output/lead_summary.json

=== 03_post_slack_digest.py ===
Headline (template):
7 new contacts this week from 7 sources: Organic search 1, Paid social 1, Paid search 1, Referral 1.
5 need a fix before routing, including 2 with no owner.

Dry run (no SLACK_WEBHOOK_URL set). This is what would be sent, also saved to output/slack_payload.json:
```

And the "Needs attention" part of the Slack message:

```text
Needs attention
• Maya Okafor (Northwind Logistics): duplicate email
• Jack Brennan: no owner; free email domain; missing company
• Tom Lindqvist (Harbour Capital): missing job title
• Maya Okafor (Northwind Logistics Ltd): no owner; duplicate email
• Sam: owner not in owner list (deactivated user?); free email domain; missing company; missing job title
```

The sample people and companies are made up.

## Cost note

With no keys, it costs nothing. HubSpot private apps and their API calls are available on HubSpot plans within the API rate limits, and a weekly pull of a few hundred contacts is a handful of calls. Slack incoming webhooks are free. With an Anthropic key, script 3 makes one short Claude call per run for the headline, so the cost is tiny; check current prices on [Anthropic's pricing page](https://www.anthropic.com/pricing).

## Swap the stack

| This repo uses | Swap for | What changes |
|---|---|---|
| HubSpot CRM search API | Salesforce | Use the REST query endpoint with SOQL (`SELECT Id, Email, ... FROM Lead WHERE CreatedDate = LAST_N_DAYS:7`) and follow `nextRecordsUrl` instead of `after` |
| HubSpot CRM search API | Attio, Pipedrive, Close | Same pattern: auth header, filtered list call, a pagination cursor. Only the field names in `flatten()` change |
| Owner list CSV | HubSpot Owners API | Replace `load_owners()` with a `GET /crm/v3/owners` call, so deactivated users show up as archived |
| Slack incoming webhook | Slack bot token | `POST https://slack.com/api/chat.postMessage` with `channel` in the body; lets you post to many channels and thread replies |
| Slack | Microsoft Teams | Teams incoming webhooks take an Adaptive Card instead of Block Kit; rewrite `build_payload()` |
| Claude headline | Any LLM or none | Swap `claude_headline()`; the template already covers "none" |
| Run by hand | n8n, cron, GitHub Actions | Schedule `python run_all.py` weekly; keep the keys in the scheduler's secrets, not in the repo |

## Customise for your stack

- **Different properties:** add them to `PROPERTIES` in script 1 and to `flatten()` in script 2 (e.g. `hs_lead_status`, `country`, or one of your custom properties)
- **Your own flags:** add a line in `add_flags()`, such as "MQL with no owner" or "country missing for EMEA routing"
- **Your owner list:** replace `sample_data/sample_owners.csv` with an export of your HubSpot users, or switch to the Owners API (see the table above)
- **A different time window:** `python 01_pull_hubspot_contacts.py --days 1` for a daily digest
- **EU portal links:** set `HUBSPOT_APP_DOMAIN=app-eu1.hubspot.com` and `HUBSPOT_PORTAL_ID` so the Slack links open the right record
- **Other objects:** change `contacts` in `SEARCH_URL` to `companies` or `deals`, and the property names to match

## How this runs today (and what production would add)

**Today:** you run three scripts by hand in a terminal. Script 1 reads from HubSpot (or sample files), script 2 writes a CSV and a summary on your laptop, and script 3 prints or posts one Slack message. It never writes to HubSpot. Keys live in a local `.env` file that Git ignores. I've tested it end to end on the sample data with no keys, and tested the retry, pagination and Slack paths against mocked HTTP responses; I haven't pointed it at a large live portal.

**Production would add:**
- A scheduler (n8n, cron or GitHub Actions) and secrets stored there, not on a laptop
- The Owners API instead of a CSV, so the owner list can't go stale
- Logging of each run (counts, errors, how long it took) somewhere you can look back at
- Tests for `flatten()` and `add_flags()` with awkward real records, and an alert when a run fails rather than silence
- A HubSpot-side fix loop: tasks or a view for the flagged records, so the digest leads to action instead of just a message
- Respecting HubSpot's search API limits (it stops paging at 10,000 results; script 1 warns you if you hit that)

See [SETUP.md](../SETUP.md) for keys, real data, and extending it.

## Pipeline outputs (current)

| File | Purpose |
| --- | --- |
| `output/contacts_raw.json` | Raw pull (mock or live) |
| `output/new_leads.csv` | Flattened + flagged |
| `output/scored_leads.csv` | Fit score + route |
| `output/crm_ready_import.csv` | Rows safe to import after review |
| `output/review_queue.csv` | Human triage |
| `output/routing_summary.json` | Digested into Slack |
| `output/slack_payload.json` | Dry-run Block Kit payload |
