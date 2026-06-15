import json

with open("/home/krit/my-office/scratch/raw_001.json", "r") as f:
    w1 = json.load(f)

with open("/home/krit/my-office/scratch/raw_002.json", "r") as f:
    w2 = json.load(f)

def sanitize(w):
    # Remove metadata that differs between workflows
    clean = {
        "nodes": [],
        "connections": {}
    }
    
    # Map node IDs and names to generic placeholders
    id_map = {}
    name_map = {}
    
    # Sort nodes by type to ensure stable mapping
    sorted_nodes = sorted(w["nodes"], key=lambda x: x.get("type", ""))
    
    for idx, n in enumerate(sorted_nodes):
        orig_id = n.get("id")
        orig_name = n.get("name")
        placeholder_id = f"node_id_{idx}"
        placeholder_name = f"node_name_{idx}"
        id_map[orig_id] = placeholder_id
        name_map[orig_name] = placeholder_name
        
    for n in sorted_nodes:
        n_clean = json.loads(json.dumps(n)) # copy
        n_clean["id"] = id_map[n_clean["id"]]
        n_clean["name"] = name_map[n_clean["name"]]
        # Remove credentials or replace with placeholder
        if "credentials" in n_clean:
            for k in n_clean["credentials"]:
                n_clean["credentials"][k] = {"id": "cred_id_placeholder", "name": "cred_name_placeholder"}
        
        # In Send a message parameters, clean guildId, channelId and content
        if n_clean.get("type") == "n8n-nodes-base.discord":
            params = n_clean.get("parameters", {})
            if "guildId" in params:
                params["guildId"] = "guild_placeholder"
            if "channelId" in params:
                params["channelId"] = "channel_placeholder"
                
        clean["nodes"].append(n_clean)
        
    # Sanitize connections using name_map
    for src, targets in w["connections"].items():
        src_placeholder = name_map.get(src, src)
        clean["connections"][src_placeholder] = {}
        for target_type, target_list in targets.items():
            clean["connections"][src_placeholder][target_type] = []
            for path in target_list:
                path_clean = []
                for step in path:
                    step_clean = json.loads(json.dumps(step))
                    step_clean["node"] = name_map.get(step_clean["node"], step_clean["node"])
                    path_clean.append(step_clean)
                clean["connections"][src_placeholder][target_type].append(path_clean)
                
    # Sort nodes and connections keys for stable comparison
    clean["nodes"] = sorted(clean["nodes"], key=lambda x: x.get("id"))
    return clean

c1 = sanitize(w1)
c2 = sanitize(w2)

# Save sanitized copies
with open("/home/krit/my-office/scratch/sanitized_001.json", "w") as f:
    json.dump(c1, f, indent=2, sort_keys=True)

with open("/home/krit/my-office/scratch/sanitized_002.json", "w") as f:
    json.dump(c2, f, indent=2, sort_keys=True)

# Check if they are equal
if c1 == c2:
    print("STRUCTURES ARE EXACTLY EQUAL!")
else:
    print("STRUCTURE DIFFERENCES FOUND!")
    # Print key differences if any
    for k in ["nodes", "connections"]:
        if c1[k] != c2[k]:
            print(f"Difference in {k}")
