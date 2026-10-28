"""Run the GTM pipeline in order: pull -> transform -> score/route -> Slack digest.

Stops if one step fails. Prefer: python pipeline.py (same thing, clearer name).
"""
import subprocess
import sys

STEPS = [
    "01_pull_hubspot_contacts.py",
    "02_transform_contacts.py",
    "04_score_and_route.py",
    "03_post_slack_digest.py",
]

for step in STEPS:
    print(f"\n=== {step} ===", flush=True)
    # Digest script may accept --dry-run style args; forward argv after script name.
    cmd = [sys.executable, step, *sys.argv[1:]] if step.startswith("03") else [sys.executable, step]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(f"{step} failed, stopping here.")
print("\nDone. Open output/scored_leads.csv, output/crm_ready_import.csv, and output/review_queue.csv.")
