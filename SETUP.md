# Setup

Everything here runs on the sample data first. Add real keys one at a time, only when you want that part to go live.

## 1. Get the code and a virtual environment

```bash
git clone https://github.com/rubianaseem/python-for-gtm-basics.git
cd python-for-gtm-basics
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

A virtual environment (`.venv`) is a private folder of Python packages just for this project, so nothing clashes with other projects. Run `source .venv/bin/activate` each time you open a new terminal for this repo; you'll see `(.venv)` at the start of the prompt.

Needs Python 3.10 or newer (`python3 --version`).

## 2. Sample run (no keys)

```bash
python run_all.py
```

You should see two pages of contacts pulled, 7 contacts flattened, 5 flagged, and a Slack message printed as a dry run. Open `output/new_leads.csv` to see the rows.

## 3. Add your keys

```bash
cp .env.example .env
```

Then open `.env` and fill in only what you have. Every value is optional.

### HubSpot private app token (script 1)

1. In HubSpot, go to **Settings → Integrations → Private Apps** (in newer portals this sits under **Development → Legacy apps**), and create a private app.
2. On **Scopes**, tick `crm.objects.contacts.read`. That's the only scope this needs; it's read-only.
3. Create the app, copy the access token, and paste it as `HUBSPOT_TOKEN=` in `.env`.
4. Optional: set `HUBSPOT_PORTAL_ID` (your Hub ID, top-right account menu) and `HUBSPOT_APP_DOMAIN` (`app-eu1.hubspot.com` for EU data centre portals) so Slack links open the contact.

Test it with a small window first: `python 01_pull_hubspot_contacts.py --days 1`.

### Slack incoming webhook (script 3)

1. Go to [api.slack.com/apps](https://api.slack.com/apps), **Create New App → From scratch**, pick your workspace.
2. Open **Incoming Webhooks**, switch it on, click **Add New Webhook to Workspace**, and choose the channel (a test channel is a good idea).
3. Copy the URL (it starts with `https://hooks.slack.com/services/`) into `SLACK_WEBHOOK_URL=`.

Run `python 03_post_slack_digest.py --dry-run` to check the message, then without `--dry-run` to post it. Treat the webhook URL like a password: anyone with it can post to that channel.

### Anthropic API key (optional, script 3)

Create a key at [console.anthropic.com](https://console.anthropic.com/) and paste it as `ANTHROPIC_API_KEY=`. Change `ANTHROPIC_MODEL` if you want a different model. If the call fails, the script tells you and uses the template.

## 4. Use your real owner list

`sample_data/sample_owners.csv` has the columns `owner_id,owner_name,team,slack_handle`. Replace it with your own: in HubSpot, **Settings → Users & Teams → Export users**, then keep the user ID, name and team columns and add Slack handles if you want them. (Or call `GET https://api.hubapi.com/crm/v3/owners` with the same token, which needs the `crm.objects.owners.read` scope.)

## 5. Run it on a schedule

Once it works by hand, schedule `python run_all.py` weekly:

- **n8n:** an Execute Command node on a self-hosted instance, or rebuild the three steps as HTTP Request + Code + Slack nodes
- **cron on a server:** `0 8 * * 1 cd /path/to/repo && .venv/bin/python run_all.py`
- **GitHub Actions:** a scheduled workflow with the keys stored as repository secrets (never commit `.env`)

## 6. Extend it with an AI coding tool

Open the folder in your tool and give it a specific ask that names the file and function. For example:

- **Cursor:** open the repo, then in chat: *"In 02_transform_contacts.py, add a flag in add_flags() for MQLs with no owner, and add the property to PROPERTIES in script 1."*
- **Claude Code:** run `claude` in the repo folder: *"Replace load_owners() with a call to the HubSpot Owners API using HUBSPOT_TOKEN, keep the CSV as the fallback when there's no token."*
- **Codex CLI:** run `codex` in the folder: *"Add a --object option to script 1 so it can pull companies or deals, and update flatten() to match."*
- **Grok:** paste a script and ask it to explain a function line by line, or to write a test for `flatten()` with a record that has every property missing.

Read every change before you run it, and run `python run_all.py` on the sample data after each one to check nothing broke.

## 7. Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'requests'` | The venv isn't active. Run `source .venv/bin/activate`, then `pip install -r requirements.txt` |
| `output/contacts_raw.json not found` | Run the scripts in order, or use `python run_all.py` |
| `HubSpot said 401 Unauthorized` | The token is wrong or was rotated. Copy it again from the private app |
| `HubSpot said 403 Forbidden` | The private app is missing `crm.objects.contacts.read` |
| Lots of `HubSpot returned 429` lines | You're near the rate limit. The script waits and retries; run it less often or narrow `--days` |
| `Slack rejected the message (404): no_service` | The webhook was removed or the URL is mistyped |
| `Slack rejected the message (400): invalid_blocks` | You edited `build_payload()` and a block is malformed. Paste `output/slack_payload.json` into Slack's Block Kit Builder to see which one |
| `Claude call failed (...)` | Bad key, no credit, or a model name that doesn't exist. The template headline is used instead |
| Every owner shows as "Unknown owner" | Your owner CSV's `owner_id` values don't match HubSpot's owner IDs; export them again |
