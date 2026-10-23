# Python for GTM: Basics

**Three small Python scripts that do the three things every GTM engineer does all week: pull records from HubSpot's API, reshape the JSON into something useful, and post the result to Slack.**

> Built by Rubia Naseem, GTM Engineer (12+ yrs CRM/RevOps, HubSpot & Salesforce).

---

## The pain point

This one comes from my own skills roadmap rather than a broken process, but it's the same gap I see RevOps people talk about. You can do a lot in HubSpot without code, and the moment you want data "out and in" between tools, the docs assume you already know how APIs work.

- *"I’m in RevOps and have two weeks time and want to learn the basics of working with the Hubspot API. Just getting data out and in from Gong, Zoominfo and so on…"* ([r/hubspot: Looking for an API course](https://www.reddit.com/r/hubspot/comments/1mczh0n/looking_for_an_api_course/))
- *"you’ll be working with HTTP methods (GET, POST, PUT, DELETE) and JSON data structures."* ([HubSpot Community: what are the programming languages I should learn to develop within hubspot?](https://community.hubspot.com/t/what-are-the-programming-languages-i-should-learn-to-develop-within-hubspot/123294/5))

---

## What it does

- **Script 1, call an API:** searches HubSpot for contacts created in the last 7 days, follows every page of results, and retries politely on rate limits
- **Script 2, transform JSON:** flattens HubSpot's nested properties into `new_leads.csv`, swaps internal values for readable labels, and joins each contact to an owner list
- **Data-quality flags:** no owner, owner not in the owner list, free email domain, missing company or job title, and duplicate emails
- **Script 3, post to Slack:** builds a Block Kit digest and posts it with an incoming webhook, or prints a dry run if there's no webhook
- **Runs with no keys:** sample API pages stand in for HubSpot, and Claude only writes the headline if you add an Anthropic key
- **Read-only:** nothing here ever writes to HubSpot

---

## Where each step runs

1. **GitHub** holds the code. Clone it or click **Code → Download ZIP**.
2. **Terminal** is where you run it: `python run_all.py`, or the three scripts one by one.
3. **HubSpot** is only read, using sample files until you add a private app token to `.env`.
4. **Claude is optional.** With an Anthropic key it writes the Slack headline; without one, a template does. It all stays in the terminal.
5. **Slack, then you.** The digest goes to your channel (or prints as a dry run), and you fix the flagged records in HubSpot by hand.

---

## Quick start

```bash
git clone https://github.com/rubianaseem/python-for-gtm-basics.git
cd python-for-gtm-basics
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run_all.py   # sample data, no keys needed
```

Everything is written to `output/`, which Git ignores so contact data never gets committed.

---

## Example output

```text
=== 01_pull_hubspot_contacts.py ===
No HUBSPOT_TOKEN set, so using the sample API pages in sample_data/ (mock mode).
Saved 7 contacts to output/contacts_raw.json

=== 02_transform_contacts.py ===
Flattened 7 contacts into output/new_leads.csv
5 contacts need attention. Summary saved to output/lead_summary.json

=== 03_post_slack_digest.py ===
Headline (template):
7 new contacts this week from 7 sources: Organic search 1, Paid social 1, Paid search 1, Referral 1.
5 need a fix before routing, including 2 with no owner.
```

The sample people and companies are made up. The full output is in [docs/DETAILS.md](docs/DETAILS.md#full-example-output).

---

## More

- [SETUP.md](SETUP.md): keys, your real owner list, scheduling, extending it with AI coding tools, troubleshooting
- [docs/WALKTHROUGH.md](docs/WALKTHROUGH.md): walk through the three scripts line by line
- [docs/DETAILS.md](docs/DETAILS.md): all the pain-point quotes, full feature list, output files, cost note, swap the stack, customising, and how this runs today vs production
