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

# 1. Load the current active workflow from n8n (on disk)
with open("/home/krit/my-office/scratch/workflow_md_current.json", "r") as f:
    wf = json.load(f)

# 2. Extract existing nodes and connections
nodes = wf["nodes"]
connections = wf["connections"]

# Remove any old version of our custom guardrail nodes if they exist
nodes = [n for n in nodes if n["name"] not in ["Guardrail Classifier", "Parse Classifier JSON", "Is In Scope IF", "Format Rejection"]]

# 3. Define the new Guardrail Classifier node
guardrail_classifier_node = {
    "parameters": {
        "promptType": "define",
        "systemPrompt": "=คุณคือระบบคัดกรองคำถามขององค์กร (Intent Classifier)\nทำหน้าที่ตรวจสอบว่าคำถามของ User ตรงกับหน้าที่ของ {{ $json.agent_name }} (ขอบเขตงาน: {{ $json.skill_set }}) หรือไม่\n\nตอบกลับเป็น JSON Format เท่านั้น ห้ามมีคำเกริ่นนำหรือคำพูดใดๆ นอกเหนือจาก JSON:\n{\n  \"is_in_scope\": true หรือ false,\n  \"reason\": \"คำอธิบายเหตุผลหรือคำแนะนำสั้นๆ ภาษาไทย\",\n  \"suggested_agent\": \"ระบุชื่อ Agent ที่เหมาะสมที่สุดหากคำถามนี้อยู่นอกเหนือขอบเขต (เลือกจาก: Project Manager, System Analyst, Dev Leader, Programmer-001 Backend, Programmer-002 Frontend, Tester-001)\"\n}",
        "text": "={{ $json.text }}",
        "options": {}
    },
    "id": "guardrail-classifier-id",
    "name": "Guardrail Classifier",
    "type": "@n8n/n8n-nodes-langchain.chainLlm",
    "position": [
        240,
        -180
    ],
    "typeVersion": 1.4
}

# 4. Define JSON Parser node
parse_json_node = {
    "parameters": {
        "jsCode": "let res = {};\nconst text = $json.text || \"\";\ntry {\n  // Find JSON block if LLM added markdown formatting\n  const jsonMatch = text.match(/\\{[\\s\\S]*?\\}/);\n  if (jsonMatch) {\n    res = JSON.parse(jsonMatch[0]);\n  } else {\n    res = JSON.parse(text);\n  }\n} catch(e) {\n  res = {\n    is_in_scope: false,\n    reason: \"ไม่สามารถประมวลผลคำสั่งเชิงเทคนิคได้โดยตรง\",\n    suggested_agent: text.toLowerCase().includes(\"frontend\") || text.includes(\"หน้าบ้าน\") ? \"Programmer-002 Frontend, UX/UI\" : \"Programmer-001 Backend\"\n  };\n}\nreturn {\n  ...$json,\n  classifier: res\n};"
    },
    "id": "parse-classifier-json-id",
    "name": "Parse Classifier JSON",
    "type": "n8n-nodes-base.code",
    "position": [
        430,
        -180
    ],
    "typeVersion": 2
}

# 5. Define IF Node to route based on scope
if_scope_node = {
    "parameters": {
        "conditions": {
            "options": {
                "caseSensitive": True,
                "leftValue": "",
                "type": "mix"
            },
            "conditions": [
                {
                    "id": "cond-in-scope",
                    "leftValue": "={{ $json.classifier.is_in_scope }}",
                    "rightValue": "true",
                    "operator": "equals",
                    "type": "string"
                }
            ],
            "combinator": "and"
        },
        "options": {}
    },
    "id": "is-in-scope-if-id",
    "name": "Is In Scope IF",
    "type": "n8n-nodes-base.if",
    "position": [
        620,
        -180
    ],
    "typeVersion": 2.1
}

# 6. Define Set node to format Rejection Message (Bypass AI Agent)
format_rejection_node = {
    "parameters": {
        "assignments": {
            "assignments": [
                {
                    "id": "as-output",
                    "name": "output",
                    "type": "string",
                    "value": "=สวัสดีครับผมในฐานะ Managing Director (MD) ขอชี้แจงว่าเรื่องนี้อยู่นอกเหนือขอบเขตหน้าที่ของผมครับ\n\n💡 คำแนะนำ: {{ $json.classifier.reason }}\n\nคุณสามารถคัดลอกข้อความด้านล่างนี้ไปสอบถาม {{ $json.classifier.suggested_agent }} ได้เลยครับ:\n```\n{{ $('Prepare AI Input').item.json.text }}\n```"
                }
            ]
        },
        "options": {}
    },
    "id": "format-rejection-id",
    "name": "Format Rejection",
    "type": "n8n-nodes-base.set",
    "position": [
        840,
        -80
    ],
    "typeVersion": 3.4
}

# Add nodes to lists
nodes.append(guardrail_classifier_node)
nodes.append(parse_json_node)
nodes.append(if_scope_node)
nodes.append(format_rejection_node)

# Position adjustments for clarity
for n in nodes:
    if n["name"] == "AI Agent":
        n["position"] = [840, -260]
    if n["name"] == "Split Message":
        n["position"] = [1060, -180]
    if n["name"] == "Send a message":
        n["position"] = [1260, -180]

# Update connections
# Remove direct connection: Prepare AI Input -> AI Agent
if "Prepare AI Input" in connections:
    connections["Prepare AI Input"]["main"] = [
        [
            {
                "node": "Guardrail Classifier",
                "type": "main",
                "index": 0
            }
        ]
    ]

# Connect Guardrail Classifier -> Parse Classifier JSON
connections["Guardrail Classifier"] = {
    "main": [
        [
            {
                "node": "Parse Classifier JSON",
                "type": "main",
                "index": 0
            }
        ]
    ]
}

# Connect Parse Classifier JSON -> Is In Scope IF
connections["Parse Classifier JSON"] = {
    "main": [
        [
            {
                "node": "Is In Scope IF",
                "type": "main",
                "index": 0
            }
        ]
    ]
}

# Connect Is In Scope IF (True branch -> index 0) to AI Agent
# Connect Is In Scope IF (False branch -> index 1) to Format Rejection
connections["Is In Scope IF"] = {
    "main": [
        [
            {
                "node": "AI Agent",
                "type": "main",
                "index": 0
            }
        ],
        [
            {
                "node": "Format Rejection",
                "type": "main",
                "index": 0
            }
        ]
    ]
}

# Connect Format Rejection -> Split Message
connections["Format Rejection"] = {
    "main": [
        [
            {
                "node": "Split Message",
                "type": "main",
                "index": 0
            }
        ]
    ]
}

# Also ensure Google Gemini Chat Model is connected to Guardrail Classifier via ai_languageModel
if "Google Gemini Chat Model" in connections:
    # Google Gemini Chat Model connects to both AI Agent and Guardrail Classifier
    connections["Google Gemini Chat Model"]["ai_languageModel"] = [
        [
            {
                "node": "AI Agent",
                "type": "ai_languageModel",
                "index": 0
            }
        ],
        [
            {
                "node": "Guardrail Classifier",
                "type": "ai_languageModel",
                "index": 0
            }
        ]
    ]

wf["nodes"] = nodes
wf["connections"] = connections

# Push update payload to n8n
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
