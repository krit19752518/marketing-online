import urllib.request
import json

api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiMDM2ZWZmNi1jNGMzLTRiMjQtYjU2My1hOGZmODFiYjE4YWYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzgwNzIwODU1fQ.cujB5QLEY2ne95TW165IHh24WjPaf_WRcY9ujjOyAf0"
base_url = "http://localhost:5678/api/v1"

headers = {
    "X-N8N-API-KEY": api_key,
    "Content-Type": "application/json"
}

req = urllib.request.Request(f"{base_url}/workflows", headers=headers)
try:
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode())
        # print workflow names and IDs
        for w in data.get("data", []):
            print(f"ID: {w.get('id')} - Name: {w.get('name')} - Active: {w.get('active')}")
except Exception as e:
    print(f"Error: {e}")
