import json
import urllib.request
import urllib.error

api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiMDM2ZWZmNi1jNGMzLTRiMjQtYjU2My1hOGZmODFiYjE4YWYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzgwNzIwODU1fQ.cujB5QLEY2ne95TW165IHh24WjPaf_WRcY9ujjOyAf0"
base_url = "http://localhost:5678/api/v1"
workflow_id = "ngHGoKsaRVwCIB5F"

headers = {
    "X-N8N-API-KEY": api_key,
    "Content-Type": "application/json"
}

# 1. Fetch the absolute current workflow from n8n API
print("Fetching current workflow from n8n...")
req_get = urllib.request.Request(f"{base_url}/workflows/{workflow_id}", headers=headers)
try:
    with urllib.request.urlopen(req_get) as res:
        wf = json.loads(res.read().decode())
except Exception as e:
    print(f"Error fetching: {e}")
    exit(1)

# 2. Extract existing nodes
nodes = wf["nodes"]

# Clean old custom nodes to prevent duplicates
nodes_to_remove = [
    "Get MD Persona", "Prepare AI Input", "Keyword Gate", "Keyword Match IF",
    "Guardrail Classifier", "Parse Classifier JSON", "Is In Scope IF", "Format Rejection"
]
nodes = [n for n in nodes if n["name"] not in nodes_to_remove]

# 3. Define all required nodes
postgres_node = {
    "parameters": {
        "operation": "executeQuery",
        "query": "SELECT agent_name, skill_set, context_data, learned_logic, keywords FROM agent_knowledge WHERE agent_id = 'MD';",
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
                },
                {
                    "id": "as-keywords",
                    "name": "keywords",
                    "type": "string",
                    "value": "={{ $json.keywords }}"
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

keyword_gate_node = {
    "parameters": {
        "jsCode": "const text = ($json.text || '').toLowerCase();\nconst keywordsStr = $json.keywords || '';\nconst keywords = keywordsStr.split(',').map(k => k.trim().toLowerCase());\n\nlet hasMatch = false;\nfor (const k of keywords) {\n  if (k && text.includes(k)) {\n    hasMatch = true;\n    break;\n  }\n}\n\nreturn {\n  ...$json,\n  keyword_matched: hasMatch\n};"
    },
    "id": "keyword-gate-node-id",
    "name": "Keyword Gate",
    "type": "n8n-nodes-base.code",
    "position": [
        260,
        16
    ],
    "typeVersion": 2
}

keyword_match_if_node = {
    "parameters": {
        "conditions": {
            "options": {
                "caseSensitive": True,
                "leftValue": "",
                "type": "mix"
            },
            "conditions": [
                {
                    "id": "cond-keyword-matched",
                    "leftValue": "={{ ($json.keyword_matched) ? 'true' : 'false' }}",
                    "rightValue": "true",
                    "operator": {
                        "type": "string",
                        "operation": "equals"
                    }
                }
            ],
            "combinator": "and"
        },
        "options": {}
    },
    "id": "keyword-match-if-node-id",
    "name": "Keyword Match IF",
    "type": "n8n-nodes-base.if",
    "position": [
        430,
        16
    ],
    "typeVersion": 2.1
}

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
        580,
        -180
    ],
    "typeVersion": 1.4
}

parse_json_node = {
    "parameters": {
        "jsCode": "let res = {};\nconst text = $json.text || \"\";\ntry {\n  const jsonMatch = text.match(/\\{[\\s\\S]*?\\}/);\n  if (jsonMatch) {\n    res = JSON.parse(jsonMatch[0]);\n  } else {\n    res = JSON.parse(text);\n  }\n} catch(e) {\n  res = {\n    is_in_scope: false,\n    reason: \"ไม่สามารถประมวลผลคำสั่งเชิงเทคนิคได้โดยตรง\",\n    suggested_agent: text.toLowerCase().includes(\"frontend\") || text.includes(\"หน้าบ้าน\") ? \"Programmer-002 Frontend, UX/UI\" : \"Programmer-001 Backend\"\n  };\n}\nreturn {\n  ...$('Prepare AI Input').item.json,\n  classifier: res\n};"
    },
    "id": "parse-classifier-json-id",
    "name": "Parse Classifier JSON",
    "type": "n8n-nodes-base.code",
    "position": [
        750,
        -180
    ],
    "typeVersion": 2
}

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
                    "leftValue": "={{ ($json.classifier && $json.classifier.is_in_scope) ? 'true' : 'false' }}",
                    "rightValue": "true",
                    "operator": {
                        "type": "string",
                        "operation": "equals"
                    }
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
        940,
        -180
    ],
    "typeVersion": 2.1
}

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
        1130,
        -80
    ],
    "typeVersion": 3.4
}

# Add the new nodes
nodes.extend([
    postgres_node, prepare_input_node, keyword_gate_node, keyword_match_if_node,
    guardrail_classifier_node, parse_json_node, if_scope_node, format_rejection_node
])

# 4. Modify existing nodes configurations
for node in nodes:
    if node["name"] == "AI Agent":
        node["position"] = [1130, -260]
        # Use systemMessage parameter (Langchain Agent node v3)
        node["parameters"] = {
            "promptType": "define",
            "systemMessage": "=คุณคือ {{ $json.agent_name }}\n\nหน้าที่และความรับผิดชอบหลักของคุณคือ:\n{{ $json.skill_set }}\n\nบริบทโครงการปัจจุบัน:\n{{ $json.context_data }}\n\nกฎเหล็กในการทำงานและการคัดกรองขอบเขตงาน:\n{{ $json.learned_logic }}\n\nโปรดตอบในภาษาเดียวกับผู้ใช้ (ภาษาไทย) และปฏิเสธอย่างสุภาพหากอยู่นอกขอบเขตงานของคุณตามสเปก",
            "text": "={{ $json.text }}",
            "options": {}
        }
    elif node["name"] == "Google Gemini Chat Model":
        # Pass systemInstruction directly to Google Gemini Model options (guarantees model compliance)
        node["parameters"] = {
            "modelName": "models/gemini-3.1-flash-lite",
            "options": {
                "systemInstruction": "=คุณคือ {{ $('Prepare AI Input').item.json.agent_name }}\n\nหน้าที่และความรับผิดชอบหลักของคุณคือ:\n{{ $('Prepare AI Input').item.json.skill_set }}\n\nบริบทโครงการปัจจุบัน:\n{{ $('Prepare AI Input').item.json.context_data }}\n\nกฎเหล็กในการทำงานและการคัดกรองขอบเขตงาน:\n{{ $('Prepare AI Input').item.json.learned_logic }}\n\nโปรดตอบในภาษาเดียวกับผู้ใช้ (ภาษาไทย) และปฏิเสธอย่างสุภาพหากอยู่นอกขอบเขตงานของคุณตามสเปก"
            }
        }
    elif node["name"] == "Simple Memory":
        node["parameters"] = {
            "sessionId": "={{ $json.sessionId }}"
        }
    elif node["name"] == "Split Message":
        node["position"] = [1350, -180]
    elif node["name"] == "Send a message":
        node["position"] = [1550, -180]

# 5. Define connections
connections = wf["connections"]

# Ensure trigger cleanup
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

# Connect Get MD Persona -> Prepare AI Input
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

# Connect Prepare AI Input -> Keyword Gate
connections["Prepare AI Input"] = {
    "main": [
        [
            {
                "node": "Keyword Gate",
                "type": "main",
                "index": 0
            }
        ]
    ]
}

# Connect Keyword Gate -> Keyword Match IF
connections["Keyword Gate"] = {
    "main": [
        [
            {
                "node": "Keyword Match IF",
                "type": "main",
                "index": 0
            }
        ]
    ]
}

# Connect Keyword Match IF: True (direct to AI Agent), False (to Classifier)
connections["Keyword Match IF"] = {
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
                "node": "Guardrail Classifier",
                "type": "main",
                "index": 0
            }
        ]
    ]
}

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

# Connect Is In Scope IF: True -> AI Agent, False -> Format Rejection
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

# Connect AI Agent -> Split Message (main)
connections["AI Agent"] = {
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

# Connect Format Rejection -> Split Message (main)
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

# Connect Split Message -> Send a message (main)
connections["Split Message"] = {
    "main": [
        [
            {
                "node": "Send a message",
                "type": "main",
                "index": 0
            }
        ]
    ]
}

# Connect Google Gemini Chat Model -> AI Agent & Guardrail Classifier (ai_languageModel)
if "Google Gemini Chat Model" in connections:
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

# Connect Simple Memory -> AI Agent (ai_memory)
if "Simple Memory" in connections:
    connections["Simple Memory"]["ai_memory"] = [
        [
            {
                "node": "AI Agent",
                "type": "ai_memory",
                "index": 0
            }
        ]
    ]

# 6. Save modified workflow and push
wf["nodes"] = nodes
wf["connections"] = connections

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
    except Exception as deact_err:
        print(f"Could not deactivate (might already be inactive): {deact_err}")

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
