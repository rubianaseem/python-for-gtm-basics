"""Run the three scripts in order: pull -> transform -> post. Stops if one fails."""
import subprocess
import sys

STEPS = ["01_pull_hubspot_contacts.py", "02_transform_contacts.py", "03_post_slack_digest.py"]

for step in STEPS:
    print(f"\n=== {step} ===", flush=True)
    result = subprocess.run([sys.executable, step, *sys.argv[1:]] if step.startswith("03") else [sys.executable, step])
    if result.returncode != 0:
        sys.exit(f"{step} failed, stopping here.")
print("\nDone. Open output/new_leads.csv to see every row.")
