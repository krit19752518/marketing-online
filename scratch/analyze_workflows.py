import json

with open("/home/krit/my-office/scratch/workflows.json", "r") as f:
    data = json.load(f)

for w in data:
    name = w["name"]
    w_id = w["id"]
    active = w["active"]
    nodes = w["nodes"]
    
    print(f"Workflow: {name} (ID: {w_id}), Active: {active}")
    trigger_nodes = [n for n in nodes if "trigger" in n.get("type", "").lower() or n.get("type", "").endswith("Trigger")]
    print(f"  Total nodes: {len(nodes)}")
    print(f"  Triggers found: {len(trigger_nodes)}")
    for tn in trigger_nodes:
        print(f"    Name: {tn.get('name')}")
        print(f"    Type: {tn.get('type')}")
        print(f"    Disabled: {tn.get('disabled', False)}")
        print(f"    Credentials: {tn.get('credentials')}")
        # print parameters keys
        print(f"    Parameters keys: {list(tn.get('parameters', {}).keys())}")
        print(f"    Parameters: {tn.get('parameters')}")
    print()
