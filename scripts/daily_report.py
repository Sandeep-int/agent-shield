from azure.data.tables import TableServiceClient
from collections import Counter
from datetime import datetime, timezone, timedelta
import os
import sys

conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
if not conn_str:
    print("ERROR: AZURE_STORAGE_CONNECTION_STRING not set.")
    sys.exit(1)

try:
    client = TableServiceClient.from_connection_string(conn_str)
    table = client.get_table_client("agentshieldlogs")

    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = list(table.query_entities(f"Timestamp ge datetime'{cutoff}'"))
except Exception as e:
    print(f"ERROR: Azure connection failed — {e}")
    sys.exit(1)

total = len(rows)
blocked = sum(1 for r in rows if r.get("verdict") == "BLOCK")
allowed = sum(1 for r in rows if r.get("verdict") == "ALLOW")
missed = sum(1 for r in rows if r.get("verdict") == "MISSED")
block_rate = (blocked / total * 100) if total else 0

layer_counts = Counter(r.get("layer_hit", "UNKNOWN") for r in rows if r.get("verdict") == "BLOCK")
top_layers = layer_counts.most_common(5)

avg_latency = sum(float(r.get("latency_ms", 0)) for r in rows) / total if total else 0

report = f"""# Agent Shield — Daily Report
**Generated:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}

## Summary
| Metric | Value |
|--------|-------|
| Total Requests (24h) | {total} |
| Blocked | {blocked} |
| Allowed | {allowed} |
| Missed (Feedback) | {missed} |
| Block Rate | {block_rate:.1f}% |
| Avg Latency | {avg_latency:.0f}ms |

## Top Attack Layers
| Layer | Count |
|-------|-------|
"""

for layer, count in top_layers:
    report += f"| {layer} | {count} |\n"

os.makedirs("reports", exist_ok=True)
with open("reports/daily_report.md", "w") as f:
    f.write(report)

print(report)
print("Saved to reports/daily_report.md")
