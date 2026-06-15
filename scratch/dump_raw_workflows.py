import json

with open("/home/krit/my-office/scratch/workflows.json", "r") as f:
    data = json.load(f)

w_001 = next(w for w in data if w["id"] == "ngHGoKsaRVwCIB5F")
w_002 = next(w for w in data if w["id"] == "HNXD2yGYOXf46QaO")

with open("/home/krit/my-office/scratch/raw_001.json", "w") as f:
    json.dump(w_001, f, indent=2, sort_keys=True)

with open("/home/krit/my-office/scratch/raw_002.json", "w") as f:
    json.dump(w_002, f, indent=2, sort_keys=True)

print("Dumped raw_001.json and raw_002.json")
