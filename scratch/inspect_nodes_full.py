import json

with open("/home/krit/my-office/scratch/workflows.json", "r") as f:
    data = json.load(f)

for w in data:
    if "Agent-" not in w["name"]:
        continue
    print(f"=== Workflow: {w['name']} ({w['id']}) ===")
    
    # Check trigger nodes
    trigger_nodes = [n for n in w["nodes"] if "trigger" in n.get("type", "").lower() or n.get("type", "").endswith("Trigger")]
    print("Trigger Nodes:")
    for tn in trigger_nodes:
        print(f"  Name: {tn.get('name')}, Type: {tn.get('type')}, Disabled: {tn.get('disabled', False)}")
        
    # Check all node names and types
    print("All Nodes:")
    for n in w["nodes"]:
        print(f"  - {n.get('name')} (Type: {n.get('type')}, Disabled: {n.get('disabled', False)})")
        
    # Check connections
    connections = w["connections"]
    print(f"Connections count: {len(connections)}")
    # Print the connection keys
    for source, targets in connections.items():
        print(f"  From node: {source}")
        for target_type, target_list in targets.items():
            for t in target_list:
                for target_item in t:
                    print(f"    To: {target_item.get('node')} ({target_item.get('type')})")
    print("\n")
