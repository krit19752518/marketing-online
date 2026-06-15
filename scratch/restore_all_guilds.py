import json
import urllib.request
import urllib.error

api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiMDM2ZWZmNi1jNGMzLTRiMjQtYjU2My1hOGZmODFiYjE4YWYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzgwNzIwODU1fQ.cujB5QLEY2ne95TW165IHh24WjPaf_WRcY9ujjOyAf0"
base_url = "http://localhost:5678/api/v1"

headers = {
    "X-N8N-API-KEY": api_key,
    "Content-Type": "application/json"
}

workflow_ids = {
    "ngHGoKsaRVwCIB5F": "Managing Director (MD)",
    "HNXD2yGYOXf46QaO": "Project Manager (PM)",
    "1dCpt5tPT5pbRdFF": "System Analyst (SA)",
    "QoXnj681VGD80MjO": "Dev Leader",
    "AiIax4SxYvDOfUH4": "Programmer-001 Backend",
    "KaeBfZ35AmRT9MNn": "Programmer-002 Frontend",
    "vE9Cbemtx9niys3g": "Tester-001"
}

guild_param = {
    "__rl": True,
    "mode": "list",
    "value": "1512432308152434708",
    "cachedResultUrl": "https://discord.com/channels/1512432308152434708",
    "cachedResultName": "Tin-Tin's server"
}

for w_id, name in workflow_ids.items():
    print(f"Restoring guildId for: {name} ({w_id})...")
    # Fetch
    req_get = urllib.request.Request(f"{base_url}/workflows/{w_id}", headers=headers)
    try:
        with urllib.request.urlopen(req_get) as res:
            wf = json.loads(res.read().decode())
    except Exception as e:
        print(f"  Error fetching: {e}")
        continue

    # Modify
    modified = False
    for node in wf["nodes"]:
        if node["name"] == "Send a message":
            node["parameters"]["guildId"] = guild_param
            modified = True
            print("  Restored guildId parameter.")

    if modified:
        payload = {
            "name": wf["name"],
            "nodes": wf["nodes"],
            "connections": wf["connections"],
            "settings": wf.get("settings", {})
        }
        try:
            # Deactivate
            req_deact = urllib.request.Request(f"{base_url}/workflows/{w_id}/deactivate", headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req_deact) as r:
                    pass
            except Exception:
                pass
            # Put
            req_put = urllib.request.Request(
                f"{base_url}/workflows/{w_id}",
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="PUT"
            )
            with urllib.request.urlopen(req_put) as res:
                print(f"  Successfully updated. Status: {res.status}")
                
            # Activate
            req_act = urllib.request.Request(f"{base_url}/workflows/{w_id}/activate", headers=headers, method="POST")
            with urllib.request.urlopen(req_act) as res_act:
                print(f"  Successfully activated. Status: {res_act.status}")
        except Exception as e:
            print(f"  Error updating/activating: {e}")
