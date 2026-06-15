import json

with open("/home/krit/my-office/scratch/workflows.json", "r") as f:
    data = json.load(f)

w_001 = next(w for w in data if w["id"] == "ngHGoKsaRVwCIB5F")
w_002 = next(w for w in data if w["id"] == "HNXD2yGYOXf46QaO")

nodes_001 = sorted(w_001["nodes"], key=lambda x: x.get("id"))
nodes_002 = sorted(w_002["nodes"], key=lambda x: x.get("id"))

print(f"Workflow 1 has {len(nodes_001)} nodes, Workflow 2 has {len(nodes_002)} nodes")

# Compare keys, types and settings of each node
for n1, n2 in zip(nodes_001, nodes_002):
    print(f"\nNode {n1.get('name')} ({n1.get('id')}):")
    if n1.get("type") != n2.get("type"):
        print(f"  Type mismatch: {n1.get('type')} vs {n2.get('type')}")
    else:
        print(f"  Type: {n1.get('type')}")
        
    # Check parameters
    p1 = n1.get("parameters", {})
    p2 = n2.get("parameters", {})
    if p1 != p2:
        print("  Parameters mismatch!")
        print("    W1:", p1)
        print("    W2:", p2)
    else:
        print("  Parameters match.")
        
    # Check credentials keys
    c1 = n1.get("credentials", {})
    c2 = n2.get("credentials", {})
    if c1.keys() != c2.keys():
        print(f"  Credentials keys mismatch: {list(c1.keys())} vs {list(c2.keys())}")
    else:
        print(f"  Credentials keys match: {list(c1.keys())}")
