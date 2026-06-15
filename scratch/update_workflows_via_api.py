import urllib.request
import json

api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiMDM2ZWZmNi1jNGMzLTRiMjQtYjU2My1hOGZmODFiYjE4YWYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzgwNzIwODU1fQ.cujB5QLEY2ne95TW165IHh24WjPaf_WRcY9ujjOyAf0"
base_url = "http://localhost:5678/api/v1"

headers = {
    "X-N8N-API-KEY": api_key,
    "Content-Type": "application/json"
}

with open("/home/krit/my-office/scratch/workflows.json", "r") as f:
    workflows = json.load(f)

for w in workflows:
    name = w["name"]
    w_id = w["id"]
    
    if "Agent-00" not in name or name == "Agent-001 : Managing Director":
        continue
        
    print(f"Updating workflow: {name} (ID: {w_id})")
    
    # Prepare payload for PUT
    # n8n expects: name, nodes, connections, settings, staticData, meta, tags, pinData
    payload = {
        "name": w["name"],
        "nodes": w["nodes"],
        "connections": w["connections"],
        "settings": w.get("settings", {})
    }
    
    req_put = urllib.request.Request(
        f"{base_url}/workflows/{w_id}",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="PUT"
    )
    
    try:
        with urllib.request.urlopen(req_put) as res:
            print(f"  Successfully updated: {res.status}")
            
        # Try to activate
        print(f"  Activating {name}...")
        req_act = urllib.request.Request(
            f"{base_url}/workflows/{w_id}/activate",
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req_act) as res_act:
            print(f"    Successfully activated: {res_act.status}")
            
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error: {e.code} - {e.reason}")
        try:
            print(f"    Response body: {e.read().decode()}")
        except Exception:
            pass
    except Exception as e:
        print(f"  Error: {e}")
    print()
