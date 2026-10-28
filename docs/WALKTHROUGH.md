# Walkthrough: judgment in a GTM Python pipeline

## The shape

```text
01 pull (paginate + retry) -> 02 transform (join + flags) -> 04 score/route -> 03 Slack digest
```

`pipeline.py` / `run_all.py` run that order. Each numbered file stays small so you can read it.

## Why retries live in the pull step

HubSpot returns `429` under burst load and paginates with `paging.next.after`. If you stop after page one, every downstream score is wrong and you will not notice. Script 01 retries politely and follows cursors; the mock pages in `sample_data/` show the same shape the live API returns.

## Why flags beat silent cleans

Script 02 does not "fix" disposable emails or invent owners. It flags them. Free-email founders can still be real; disposable domains and invalid addresses should not enter an SDR sequence. Duplicate emails (case variants in the sample) need a human merge decision.

## Why a review queue exists

Script 04 scores ICP fit and routes rows. Quarantine / review rows go to `output/review_queue.csv`. Only non-quarantine routes land in `crm_ready_import.csv`. That split is the whole point: automation proposes, humans accept, CRM stays trustworthy.

## Routing rules you should edit

`sample_data/routing_rules.json` holds ICP countries, title keywords, score weights, and thresholds. Change those before you trust scores on your own data.

## Slack is last on purpose

The digest reads both `lead_summary.json` and `routing_summary.json` so the channel sees volume *and* route mix. Dry-run without a webhook so you can paste the payload into Slack's Block Kit Builder.
