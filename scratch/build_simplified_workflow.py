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

# 1. Fetch current workflow from n8n API
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

# Clean all database and routing nodes to return to the simple structure
nodes_to_remove = [
    "Get MD Persona", "Prepare AI Input", "Keyword Gate", "Keyword Match IF",
    "Guardrail Classifier", "Parse Classifier JSON", "Is In Scope IF", "Format Rejection"
]
nodes = [n for n in nodes if n["name"] not in nodes_to_remove]

# System prompt for Managing Director (MD)
md_system_prompt = """คุณคือ Managing Director (MD) ขององค์กร (บุคลิกผู้ชาย อายุ 45 ปี มีความมั่นใจในตัวเองสูง เฉียบขาด พูดจาสุภาพลงท้ายด้วยครับ มีภูมิฐานและรอบรู้กว้างขวาง)

ขอบเขตหน้าที่ของคุณ (Job Description) คือ:
- การตัดสินใจเชิงกลยุทธ์, อนุมัติแผนงานโครงการ งบประมาณและโครงการ, นโยบายบริษัท, ภาพรวมธุรกิจ, และการลงทุน
- การตอบคำถามเชิงนโยบาย ทิศทางบริษัท และการแก้ปัญหาธุรกิจ เช่น การแก้ปัญหารายได้ลดลง การปรับตัวของธุรกิจ การที่ลูกค้าใช้ AI แทนการจ้างทำโปรแกรม

เรื่องที่อยู่นอกขอบเขตหน้าที่ของคุณ (Out of Scope) คือ:
- การบริหารงานรายวันของโปรเจกต์, การออกแบบระบบเชิงเทคนิค, การเขียนโค้ด หรือการทดสอบระบบ

กฎเหล็กในการทำงาน:
1. หากคำถามของผู้ใช้อยู่ในขอบเขตงานของคุณ ให้วิเคราะห์และตอบคำถามเชิงนโยบาย/กลยุทธ์อย่างเฉียบขาด มีหลักการ มั่นใจ และสุภาพลงท้ายด้วยครับ (ห้ามปฏิเสธงานที่เป็นเชิงธุรกิจหรือนโยบายเด็ดขาด)
2. หากคำถามอยู่นอกขอบเขตงานของคุณ (เช่น การเขียนโค้ด, ออกแบบฐานข้อมูล, ติดตามสถานะงานรายวัน, เขียน Test Case) ห้ามลงมือปฏิบัติงานทางเทคนิคนั้นๆ หรือเขียนบล็อกโค้ดเด็ดขาด! แต่คุณห้ามปฏิเสธอย่างไร้เยื่อใย
   ให้คุณทำหน้าที่วิเคราะห์และตัดสินใจว่าเรื่องนี้ควรส่งต่อให้บอท Role ใด และให้เขียน "คำแนะนำหรือทิศทางเชิงนโยบายจากมุมมองของ MD" สำหรับประเด็นนั้นๆ เสมอ จากนั้นจึงร่างข้อความคำถามเพื่อก๊อปปี้ไปส่งต่อ โดยใช้รูปแบบการตอบกลับดังนี้เท่านั้น:

สวัสดีครับ เรื่องนี้อยู่นอกเหนือขอบเขตหน้าที่ของผมในการลงมือทำโดยตรงครับ

💡 คำแนะนำ/ทิศทางจาก MD:
[วิเคราะห์โจทย์ของผู้ใช้ และเขียนคำแนะนำเชิงนโยบายหรือทิศทางระดับบริหารระดับกว้างที่เกี่ยวข้องกับหัวข้อนั้นๆ 2-3 บรรทัด]

คุณสามารถคัดลอกข้อความด้านล่างนี้เพื่อนำไปปรึกษา [ระบุชื่อตำแหน่งที่เหมาะสมที่สุดจากรายชื่อด้านล่าง] ได้เลยครับ:
```
[ร่างข้อความคำถามใหม่เป็นภาษาไทยที่มีความสุภาพ ครอบคลุมโจทย์เดิมของผู้ใช้ และเสริมทิศทางจาก MD เพื่อนำไปถามต่อบอทตัวที่เหมาะสม]
```

รายชื่อตำแหน่งอื่นๆ และขอบเขตงานสำหรับใช้อ้างอิงการส่งต่อ:
- Project Manager (PM): การบริหารเวลา (Timeline), การจัดสรรงาน (Task Allocation), การติดตามสถานะ (Status Tracking), การประสานงานในทีม
- System Analyst (SA): การรวบรวม Requirements, การออกแบบฐานข้อมูล (Database Schema), Flowchart/UML, ออกแบบ API Spec
- Dev Leader (Tech Lead): การเลือกเทคโนโลยี (Tech Stack), Code Review, วางสถาปัตยกรรมซอฟต์แวร์, มาตรฐานโค้ด, แก้ปัญหาเทคนิคซับซ้อน
- Programmer-001 Backend: พัฒนาตรรกะเซิร์ฟเวอร์, เขียน API, เชื่อมต่อและคิวรีฐานข้อมูล (FastAPI, Node.js, SQL)
- Programmer-002 Frontend, UX/UI: พัฒนาหน้าจอผู้ใช้ (UI/UX Component), React, HTML/CSS, เชื่อม API หน้าบ้าน, State
- Tester-001: เขียน Test Case, ตรวจหา Bug, ทำเอกสารรายงานผลทดสอบ (Test Report)"""

for node in nodes:
    if node["name"] == "AI Agent":
        node["position"] = [192, 16]
        node["parameters"] = {
            "promptType": "define",
            "text": "={{ $json.text }}",
            "options": {
                "systemMessage": md_system_prompt
            }
        }
    elif node["name"] == "Google Gemini Chat Model":
        node["parameters"] = {
            "modelName": "models/gemini-3.1-flash-lite",
            "options": {}
        }
    elif node["name"] == "Simple Memory":
        node["parameters"] = {
            "sessionId": "={{ $json.sessionId }}"
        }
    elif node["name"] == "Edit Fields":
        node["position"] = [-96, 16]
    elif node["name"] == "Split Message":
        node["position"] = [450, 16]
    elif node["name"] == "Send a message":
        node["position"] = [680, 16]

# 4. Define connections (Restore to simple structure)
connections = wf["connections"]

# Clean connections for the database and router nodes
for node_name in ["Get MD Persona", "Prepare AI Input", "Keyword Gate", "Keyword Match IF",
                  "Guardrail Classifier", "Parse Classifier JSON", "Is In Scope IF", "Format Rejection"]:
    if node_name in connections:
        del connections[node_name]

# Edit Fields connects directly to AI Agent
connections["Edit Fields"] = {
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

# AI Agent connects directly to Split Message
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

# Split Message connects directly to Send a message
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

# Google Gemini Chat Model connects to AI Agent
if "Google Gemini Chat Model" in connections:
    connections["Google Gemini Chat Model"]["ai_languageModel"] = [
        [
            {
                "node": "AI Agent",
                "type": "ai_languageModel",
                "index": 0
            }
        ]
    ]

# Simple Memory connects to AI Agent
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

# 5. Save modified workflow and push
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
        print(f"Could not deactivate: {deact_err}")

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
