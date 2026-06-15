import urllib.request
import json

api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiMDM2ZWZmNi1jNGMzLTRiMjQtYjU2My1hOGZmODFiYjE4YWYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzgwNzIwODU1fQ.cujB5QLEY2ne95TW165IHh24WjPaf_WRcY9ujjOyAf0"
base_url = "http://localhost:5678/api/v1"

headers = {
    "X-N8N-API-KEY": api_key,
    "Content-Type": "application/json"
}

# List of workflow IDs to check
workflow_ids = [
    "HNXD2yGYOXf46QaO", # Agent-002
    "1dCpt5tPT5pbRdFF", # Agent-003
    "QoXnj681VGD80MjO", # Agent-004
    "AiIax4SxYvDOfUH4", # Agent-005
    "KaeBfZ35AmRT9MNn", # Agent-006
    "vE9Cbemtx9niys3g"  # Agent-007
]

for w_id in workflow_ids:
    print(f"Checking workflow: {w_id}")
    # Get current status
    req = urllib.request.Request(f"{base_url}/workflows/{w_id}", headers=headers)
    try:
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode())
            print(f"  Name: {data.get('name')}, Active: {data.get('active')}")
            
            # Deactivate first if active, then activate to trigger clean gateway initialization
            if data.get('active'):
                print(f"  Deactivating {w_id}...")
                deact_req = urllib.request.Request(
                    f"{base_url}/workflows/{w_id}/deactivate",
                    headers=headers,
                    method="POST"
                )
                with urllib.request.urlopen(deact_req) as deact_res:
                    print(f"    Deactivated: {deact_res.status}")
            
            print(f"  Activating {w_id}...")
            act_req = urllib.request.Request(
                f"{base_url}/workflows/{w_id}/activate",
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(act_req) as act_res:
                print(f"    Activated: {act_res.status}")
                
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error on {w_id}: {e.code} - {e.reason}")
        try:
            error_body = e.read().decode()
            print(f"    Body: {error_body}")
        except Exception as read_err:
            print(f"    Failed to read body: {read_err}")
    except Exception as e:
        print(f"  Error on {w_id}: {e}")
