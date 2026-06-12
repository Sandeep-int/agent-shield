from azure.data.tables import TableServiceClient
import pandas as pd
import os

conn_str = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
client = TableServiceClient.from_connection_string(conn_str)
table = client.get_table_client("agentshieldlogs")

entities = list(table.list_entities())
rows = [dict(e) for e in entities]

df = pd.DataFrame(rows)

cols = ["prompt", "verdict", "layer_hit", "timestamp"]
df = df[[c for c in cols if c in df.columns]]

blocked = df[df["verdict"] == "BLOCK"]
allowed = df[df["verdict"] == "ALLOW"]

blocked.to_csv("data/blocked_prompts.csv", index=False)
allowed.to_csv("data/allowed_prompts.csv", index=False)
df.to_csv("data/all_prompts.csv", index=False)

print(f"Total   : {len(df)}")
print(f"Blocked : {len(blocked)}")
print(f"Allowed : {len(allowed)}")
