import json

with open("/home/krit/my-office/scratch/workflows.json", "r") as f:
    data = json.load(f)

w_001 = next(w for w in data if w["id"] == "ngHGoKsaRVwCIB5F")
w_002 = next(w for w in data if w["id"] == "HNXD2yGYOXf46QaO")

node_001_trigger = next(n for n in w_001["nodes"] if n["type"] == "n8n-nodes-discord-trigger.discordTrigger")
node_002_trigger = next(n for n in w_002["nodes"] if n["type"] == "n8n-nodes-discord-trigger.discordTrigger")

print("Agent-001 Trigger Node:")
print(json.dumps(node_001_trigger, indent=2))
print("\nAgent-002 Trigger Node:")
print(json.dumps(node_002_trigger, indent=2))
