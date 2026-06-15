import json

with open("/home/krit/my-office/scratch/workflows.json", "r") as f:
    data = json.load(f)

for w in data:
    if "Agent-" not in w["name"]:
        continue
    print(f"=== Workflow: {w['name']} ({w['id']}) ===")
    for n in w["nodes"]:
        if n.get("credentials"):
            print(f"  Node: {n.get('name')} (Type: {n.get('type')})")
            print(f"    Credentials: {n.get('credentials')}")
    print()
