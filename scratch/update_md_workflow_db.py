import json
import urllib.request
import urllib.error

# API credentials and configuration
api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiMDM2ZWZmNi1jNGMzLTRiMjQtYjU2My1hOGZmODFiYjE4YWYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzgwNzIwODU1fQ.cujB5QLEY2ne95TW165IHh24WjPaf_WRcY9ujjOyAf0"
base_url = "http://localhost:5678/api/v1"
workflow_id = "ngHGoKsaRVwCIB5F"

headers = {
    "X-N8N-API-KEY": api_key,
    "Content-Type": "application/json"
}

# 1. Load the original fetched workflow JSON
with open("/home/krit/my-office/scratch/workflow_md.json", "r") as f:
    wf = json.load(f)

# 2. Define nodes to insert/modify
postgres_node = {
    "parameters": {
        "operation": "executeQuery",
        "query": "SELECT agent_name, skill_set, context_data, learned_logic FROM agent_knowledge WHERE agent_id = 'MD';",
        "options": {}
    },
    "id": "postgres-get-md-persona-id",
    "name": "Get MD Persona",
    "type": "n8n-nodes-base.postgres",
    "position": [
        8,
        16
    ],
    "typeVersion": 2.6,
    "credentials": {
        "postgres": {
            "id": "PEIuFXuORvNgS8U7",
            "name": "Postgres account"
        }
    }
}

prepare_input_node = {
    "parameters": {
        "assignments": {
            "assignments": [
                {
                    "id": "as-text",
                    "name": "text",
                    "type": "string",
                    "value": "={{ $('Edit Fields').item.json.text }}"
                },
                {
                    "id": "as-sessionId",
                    "name": "sessionId",
                    "type": "string",
                    "value": "={{ $('Edit Fields').item.json.sessionId }}"
                },
                {
                    "id": "as-agent_name",
                    "name": "agent_name",
                    "type": "string",
                    "value": "={{ $json.agent_name }}"
                },
                {
                    "id": "as-skill_set",
                    "name": "skill_set",
                    "type": "string",
                    "value": "={{ $json.skill_set }}"
                },
                {
                    "id": "as-context_data",
                    "name": "context_data",
                    "type": "string",
                    "value": "={{ $json.context_data }}"
                },
                {
                    "id": "as-learned_logic",
                    "name": "learned_logic",
                    "type": "string",
                    "value": "={{ $json.learned_logic }}"
                }
            ]
        },
        "options": {}
    },
    "id": "set-prepare-ai-input-id",
    "name": "Prepare AI Input",
    "type": "n8n-nodes-base.set",
    "position": [
        112,
        16
    ],
    "typeVersion": 3.4
}

# Update nodes list (avoid duplicates)
nodes = wf["nodes"]
nodes = [n for n in nodes if n["name"] not in ["Get MD Persona", "Prepare AI Input"]]
nodes.append(postgres_node)
nodes.append(prepare_input_node)

# Update AI Agent and Simple Memory node parameters
for node in nodes:
    if node["name"] == "AI Agent":
        node["position"] = [240, 16]
        node["parameters"] = {
            "promptType": "define",
            "systemMessage": "=คุณคือ {{ $json.agent_name }}\n\nหน้าที่และความรับผิดชอบหลักของคุณคือ:\n{{ $json.skill_set }}\n\nบริบทโครงการปัจจุบัน:\n{{ $json.context_data }}\n\nกฎเหล็กในการทำงานและการคัดกรองขอบเขตงาน:\n{{ $json.learned_logic }}\n\nโปรดตอบในภาษาเดียวกับผู้ใช้ (ภาษาไทย) และปฏิเสธอย่างสุภาพหากอยู่นอกขอบเขตงานของคุณตามสเปก",
            "text": "={{ $json.text }}",
            "options": {}
        }
    if node["name"] == "Google Gemini Chat Model":
        node["parameters"] = {
            "modelName": "models/gemini-3.1-flash-lite",
            "options": {
                "systemInstruction": "=คุณคือ {{ $('Prepare AI Input').item.json.agent_name }}\n\nหน้าที่และความรับผิดชอบหลักของคุณคือ:\n{{ $('Prepare AI Input').item.json.skill_set }}\n\nบริบทโครงการปัจจุบัน:\n{{ $('Prepare AI Input').item.json.context_data }}\n\nกฎเหล็กในการทำงานและการคัดกรองขอบเขตงาน:\n{{ $('Prepare AI Input').item.json.learned_logic }}\n\nโปรดตอบในภาษาเดียวกับผู้ใช้ (ภาษาไทย) และปฏิเสธอย่างสุภาพหากอยู่นอกขอบเขตงานของคุณตามสเปก"
            }
        }
    if node["name"] == "Simple Memory":
        node["parameters"] = {
            "sessionKey": "={{ $json.sessionId }}"
        }

# 3. Update connections
connections = wf["connections"]

# Route: Edit Fields -> Get MD Persona -> Prepare AI Input -> AI Agent
if "Edit Fields" in connections:
    connections["Edit Fields"]["main"] = [
        [
            {
                "node": "Get MD Persona",
                "type": "main",
                "index": 0
            }
        ]
    ]

connections["Get MD Persona"] = {
    "main": [
        [
            {
                "node": "Prepare AI Input",
                "type": "main",
                "index": 0
            }
        ]
    ]
}

connections["Prepare AI Input"] = {
    "main": [
        [
            {
                "node": "AI Agent",
                "type": "main",
                "index": 0
            }
        ]
    ]
}

wf["nodes"] = nodes
wf["connections"] = connections

# 4. Push update to n8n
payload = {
    "name": wf["name"],
    "nodes": wf["nodes"],
    "connections": wf["connections"],
    "settings": wf.get("settings", {})
}

req_put = urllib.request.Request(
    f"{base_url}/workflows/{workflow_id}",
    data=json.dumps(payload).encode("utf-8"),
    headers=headers,
    method="PUT"
)

try:
    with urllib.request.urlopen(req_put) as res:
        print(f"Successfully updated workflow on n8n. Status code: {res.status}")
        
    # Activate the workflow
    print("Activating the updated workflow...")
    req_act = urllib.request.Request(
        f"{base_url}/workflows/{workflow_id}/activate",
        headers=headers,
        method="POST"
    )
    with urllib.request.urlopen(req_act) as res_act:
        print(f"Workflow successfully activated! Status code: {res_act.status}")
        
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} - {e.reason}")
    print(e.read().decode())
except Exception as e:
    print(f"Error occurred: {e}")
