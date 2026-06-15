import urllib.request
import json

api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiMDM2ZWZmNi1jNGMzLTRiMjQtYjU2My1hOGZmODFiYjE4YWYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzgwNzIwODU1fQ.cujB5QLEY2ne95TW165IHh24WjPaf_WRcY9ujjOyAf0"
base_url = "http://localhost:5678/api/v1"

headers = {
    "X-N8N-API-KEY": api_key,
    "Content-Type": "application/json"
}

cred_ids = [
    "KXXGCmAlix0gbmRx", # Agent-001 trigger
    "YweoqNhurLiUgjm4", # Agent-002 trigger
]

req = urllib.request.Request(f"{base_url}/credentials", headers=headers)
try:
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode())
        print(json.dumps(data, indent=2))
except Exception as e:
    print(f"  Error: {e}")
