import json

with open("/home/krit/my-office/scratch/workflows.json", "r") as f:
    data = json.load(f)

w_001 = next(w for w in data if w["id"] == "ngHGoKsaRVwCIB5F")
w_002 = next(w for w in data if w["id"] == "HNXD2yGYOXf46QaO")

print("Agent-001 Connections:")
print(json.dumps(w_001["connections"], indent=2))
print("\nAgent-002 Connections:")
print(json.dumps(w_002["connections"], indent=2))
