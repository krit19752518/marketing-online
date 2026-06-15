import json
import urllib.request
import urllib.error

api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiMDM2ZWZmNi1jNGMzLTRiMjQtYjU2My1hOGZmODFiYjE4YWYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzgwNzIwODU1fQ.cujB5QLEY2ne95TW165IHh24WjPaf_WRcY9ujjOyAf0"
base_url = "http://localhost:5678/api/v1"
workflow_id = "HNXD2yGYOXf46QaO" # Agent-002 : Project Manager

headers = {
    "X-N8N-API-KEY": api_key,
    "Content-Type": "application/json"
}

# 1. Fetch current PM workflow
print("Fetching PM workflow from n8n...")
req_get = urllib.request.Request(f"{base_url}/workflows/{workflow_id}", headers=headers)
try:
    with urllib.request.urlopen(req_get) as res:
        wf = json.loads(res.read().decode())
except Exception as e:
    print(f"Error fetching: {e}")
    exit(1)

# 2. Modify "Send a message" node parameters to remove guildId
nodes = wf["nodes"]
for node in nodes:
    if node["name"] == "Send a message":
        print("Found Send a message node. Current parameters:")
        print(json.dumps(node["parameters"], indent=2))
        
        # Remove guildId parameter
        if "guildId" in node["parameters"]:
            del node["parameters"]["guildId"]
            print("Removed guildId parameter.")
            
# 3. Upload modified workflow
payload = {
    "name": wf["name"],
    "nodes": wf["nodes"],
    "connections": wf["connections"],
    "settings": wf.get("settings", {})
}

try:
    print("Deactivating workflow first...")
    req_deact = urllib.request.Request(
        f"{base_url}/workflows/{workflow_id}/deactivate",
        headers=headers,
        method="POST"
    )
    try:
        with urllib.request.urlopen(req_deact) as res_deact:
            print(f"Deactivated: {res_deact.status}")
    except Exception as e:
        print(f"Could not deactivate: {e}")

    req_put = urllib.request.Request(
        f"{base_url}/workflows/{workflow_id}",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="PUT"
    )
    with urllib.request.urlopen(req_put) as res:
        print(f"Successfully updated workflow on n8n. Status: {res.status}")
        
    print("Activating the updated workflow...")
    req_act = urllib.request.Request(
        f"{base_url}/workflows/{workflow_id}/activate",
        headers=headers,
        method="POST"
    )
    with urllib.request.urlopen(req_act) as res_act:
        print(f"Workflow successfully activated! Status: {res_act.status}")
        
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} - {e.reason}")
    print(e.read().decode())
except Exception as e:
    print(f"Error occurred: {e}")
