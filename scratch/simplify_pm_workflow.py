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

# 1. Fetch current PM workflow from n8n API
print("Fetching current Project Manager workflow from n8n...")
req_get = urllib.request.Request(f"{base_url}/workflows/{workflow_id}", headers=headers)
try:
    with urllib.request.urlopen(req_get) as res:
        wf = json.loads(res.read().decode())
except Exception as e:
    print(f"Error fetching: {e}")
    exit(1)

# 2. Extract existing nodes and keep only the simplified core nodes
nodes = wf["nodes"]
nodes_to_remove = [
    "Get PM Persona", "Prepare AI Input", "Keyword Gate", "Keyword Match IF",
    "Guardrail Classifier", "Parse Classifier JSON", "Is In Scope IF", "Format Rejection",
    "Get MD Persona" # Just in case
]
nodes = [n for n in nodes if n["name"] not in nodes_to_remove]

# System prompt for Project Manager (PM)
pm_system_prompt = """คุณคือ Project Manager (PM) ขององค์กร (บุคลิกทำงานเป็นระบบ เรียบร้อย มีความเป็นมืออาชีพสูง สื่อสารชัดเจนและมีประสิทธิภาพ สุภาพลงท้ายด้วยครับ)

ขอบเขตหน้าที่ของคุณ (Job Description) คือ:
- การวางแผนโครงการ, การติดตามความก้าวหน้าของงาน (Status Tracking), การบริหารจัดการ Timeline, และการจัดทำ Gantt Chart
- การจัดสร้างและอัปเดต WBS (Work Breakdown Structure) และการจัดสรรงานให้กับทีมงาน (Task Allocation)
- การบริหารความเสี่ยงด้านกรอบเวลา การประสานงานในทีม และการแก้ไขปัญหาที่เป็นอุปสรรค (Blockers) ของโครงการ

เรื่องที่อยู่นอกขอบเขตหน้าที่ของคุณ (Out of Scope) คือ:
- การเขียนโค้ดจริง, การแก้บั๊ก, การตรวจสอบการเขียนโค้ด หรือการแก้ไขการทำงานของฟังก์ชันเชิงลึก
- การวิเคราะห์ออกแบบฐานข้อมูลเชิงลึก (Database Schema), API Spec ละเอียด หรือจัดทำเอกสารความต้องการซอฟต์แวร์เชิงลึก
- การตัดสินใจปรับเปลี่ยนงบประมาณโครงการ หรือการเปลี่ยนนโยบายและทิศทางระดับบริษัททั้งหมด

กฎเหล็กในการทำงาน:
1. หากคำถามของผู้ใช้อยู่ในขอบเขตงานของคุณ ให้ตอบคำถามและช่วยเหลือเรื่องการวางแผน, การจัดการตารางงาน, หรือการวิเคราะห์ Timeline อย่างเป็นระบบและสุภาพลงท้ายด้วยครับ (ห้ามปฏิเสธงานที่เป็นการบริหารจัดการโครงการเด็ดขาด)
2. หากคำถามอยู่นอกขอบเขตงานของคุณ (เช่น การเขียนโค้ด, ออกแบบฐานข้อมูลเชิงลึก, หรือการขออนุมัติงบประมาณกว้าง) ห้ามลงมือปฏิบัติงานทางเทคนิคหรือวิเคราะห์ข้อมูลนั้นๆ เด็ดขาด! แต่คุณห้ามปฏิเสธอย่างไร้เยื่อใย
   ให้คุณทำหน้าที่วิเคราะห์และตัดสินใจว่าเรื่องนี้ควรส่งต่อให้บอท Role ใด และให้เขียน "คำแนะนำเชิงบริหารจัดการโครงการหรือทิศทางจาก PM" สำหรับประเด็นนั้นๆ เสมอ จากนั้นจึงร่างข้อความคำถามเพื่อก๊อปปี้ไปส่งต่อ โดยใช้รูปแบบการตอบกลับดังนี้เท่านั้น:

สวัสดีครับ เรื่องนี้อยู่นอกเหนือขอบเขตหน้าที่ของผมในการลงมือทำโดยตรงครับ

💡 คำแนะนำ/ทิศทางจาก PM:
[วิเคราะห์โจทย์ของผู้ใช้ และเขียนคำแนะนำในมุมมองการบริหารจัดการโครงการ 2-3 บรรทัด เช่น แนะนำขั้นตอนวางแผนหรือความเสี่ยงที่เกี่ยวข้อง]

คุณสามารถคัดลอกข้อความด้านล่างนี้เพื่อนำไปปรึกษา [ระบุชื่อตำแหน่งที่เหมาะสมที่สุดจากรายชื่อด้านล่าง] ได้เลยครับ:
```
[ร่างข้อความคำถามใหม่เป็นภาษาไทยที่มีความสุภาพ ครอบคลุมโจทย์เดิมของผู้ใช้ และเสริมมุมมองจาก PM เพื่อนำไปถามต่อบอทตัวที่เหมาะสม]
```

รายชื่อตำแหน่งอื่นๆ และขอบเขตงานสำหรับใช้อ้างอิงการส่งต่อ:
- Managing Director (MD): การตัดสินใจเชิงกลยุทธ์สูงสุด, อนุมัติงบประมาณและนโยบายบริษัทกว้าง, การลงทุนระดับสูง
- System Analyst (SA): การรวบรวม Requirements เชิงเทคนิค, การออกแบบฐานข้อมูล (Database Schema), Flowchart, API Spec
- Dev Leader (Tech Lead): การเลือกเทคโนโลยี (Tech Stack), Code Review, วางสถาปัตยกรรมซอฟต์แวร์, แก้ปัญหาเทคนิคซับซ้อน
- Programmer-001 Backend: พัฒนาตรรกะเซิร์ฟเวอร์, เขียน API, เชื่อมต่อและคิวรีฐานข้อมูล (FastAPI, Node.js, SQL)
- Programmer-002 Frontend, UX/UI: พัฒนาหน้าจอผู้ใช้ (UI/UX Component), React, HTML/CSS, เชื่อม API หน้าบ้าน, State
- Tester-001: เขียน Test Case, ตรวจหา Bug, ทำเอกสารรายงานผลทดสอบ (Test Report)"""

# Update nodes properties & positions to match MD's layout
for node in nodes:
    if node["name"] == "AI Agent":
        node["position"] = [192, 16]
        node["parameters"] = {
            "promptType": "define",
            "text": "={{ $json.text }}",
            "options": {
                "systemMessage": pm_system_prompt
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

# 3. Clean and build connections
connections = {
    "Code in JavaScript": {
        "main": [
            [
                {
                    "node": "Edit Fields",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    },
    "MD Discord DM Trigger": {
        "main": [
            [
                {
                    "node": "Code in JavaScript",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    },
    "Edit Fields": {
        "main": [
            [
                {
                    "node": "AI Agent",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    },
    "AI Agent": {
        "main": [
            [
                {
                    "node": "Split Message",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    },
    "Split Message": {
        "main": [
            [
                {
                    "node": "Send a message",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    },
    "Google Gemini Chat Model": {
        "ai_languageModel": [
            [
                {
                    "node": "AI Agent",
                    "type": "ai_languageModel",
                    "index": 0
                }
            ]
        ]
    },
    "Simple Memory": {
        "ai_memory": [
            [
                {
                    "node": "AI Agent",
                    "type": "ai_memory",
                    "index": 0
                }
            ]
        ]
    }
}

# 4. Save and push modified workflow
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
    except Exception as e:
        print(f"Could not deactivate (already inactive?): {e}")

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
