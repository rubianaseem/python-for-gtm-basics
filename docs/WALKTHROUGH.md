# Walk through it line by line: Python for GTM: Basics

The code explained step by step, so you can learn it rather than just run it. Back to the [README](../README.md).

The bits worth understanding, in the order they run.

### Script 1: `01_pull_hubspot_contacts.py`

```python
since_ms = int(since.timestamp() * 1000)
body = {"filterGroups": [{"filters": [{"propertyName": "createdate", "operator": "GTE", "value": str(since_ms)}]}], ...}
```
HubSpot's search API takes a JSON body, not URL parameters. Filters inside one `filterGroup` are ANDed; separate groups are ORed. Dates are compared as milliseconds since 1970, which is why the date gets multiplied by 1000.

```python
resp = requests.post(url, headers=headers, json=body, timeout=30)
```
`headers` carries `Authorization: Bearer <token>`. `json=body` turns the Python dict into JSON for you. `timeout=30` means a hung connection fails after 30 seconds instead of waiting forever.

```python
if resp.status_code in (429, 500, 502, 503, 504) and attempt < attempts:
    wait = int(resp.headers.get("Retry-After", 2 ** attempt))
```
`429` is HubSpot saying "too many requests". The polite thing is to wait (as long as `Retry-After` says, or 2, 4, 8 seconds) and try again, rather than crash or hammer it.

```python
after = data.get("paging", {}).get("next", {}).get("after")
if not after:
    return contacts
```
The API gives you at most 100 records per call. If there are more, the response includes `paging.next.after`, and you send that back as `"after"` to get the next page. No `after` means you're on the last page. Chaining `.get(..., {})` means a missing key gives you `None` instead of an error.

### Script 2: `02_transform_contacts.py`

```python
def clean(value) -> str:
    return (value or "").strip()
```
HubSpot sends an empty property as `null` (Python `None`) or as `""`. `value or ""` turns `None` into `""`, so every check after this only has one kind of "missing" to handle.

```python
return {row["owner_id"]: row for row in csv.DictReader(f)}
```
A dictionary comprehension: it reads the owner CSV and builds `{"7001": {...Sam Patel...}, ...}`. Looking an owner up by ID is then instant, the same idea as a VLOOKUP.

```python
seen = Counter(r["email"] for r in rows if r["email"])
...
if seen[r["email"]] > 1:
    flags.append("duplicate email")
```
`Counter` counts how many times each email appears. Emails were lower-cased in `flatten`, so `Maya.Okafor@NorthwindLogistics.com` and `maya.okafor@northwindlogistics.com` count as the same person.

```python
writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
writer.writerows(rows)
```
Each row is a dict, so `DictWriter` uses the keys as column headers. That's the whole JSON-to-CSV step.

### Script 3: `03_post_slack_digest.py`

```python
headline = claude_headline(s)
headline = headline or template_headline(s)
```
Try Claude first. `claude_headline` returns `None` if there's no key or the call fails, and `or` falls back to the template. The prompt only passes the counts and tells Claude to invent nothing.

```python
{"type": "section", "text": {"type": "mrkdwn", "text": headline}}
```
Slack messages are built from "blocks". `mrkdwn` is Slack's own Markdown (`*bold*`, `<url|label>` for links). The top-level `"text"` is the fallback shown in notifications.

```python
if resp.status_code != 200 or resp.text.strip() != "ok":
```
A Slack incoming webhook replies with the plain text `ok` when it worked. Anything else is an error message worth printing.
