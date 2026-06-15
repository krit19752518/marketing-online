import json
import urllib.request
import urllib.error

api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiMDM2ZWZmNi1jNGMzLTRiMjQtYjU2My1hOGZmODFiYjE4YWYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzgwNzIwODU1fQ.cujB5QLEY2ne95TW165IHh24WjPaf_WRcY9ujjOyAf0"
base_url = "http://localhost:5678/api/v1"
workflow_id = "vE9Cbemtx9niys3g" # Agent-007 : Tester-001

headers = {
    "X-N8N-API-KEY": api_key,
    "Content-Type": "application/json"
}

# 1. Fetch current Tester-001 workflow from n8n API
print("Fetching current Tester-001 workflow from n8n...")
req_get = urllib.request.Request(f"{base_url}/workflows/{workflow_id}", headers=headers)
try:
    with urllib.request.urlopen(req_get) as res:
        wf = json.loads(res.read().decode())
except Exception as e:
    print(f"Error fetching: {e}")
    exit(1)

# Save a backup locally
with open("/home/krit/my-office/scratch/workflow_tester_backup.json", "w") as f:
    json.dump(wf, f, indent=2)

# 2. Extract existing nodes and keep only the simplified core nodes
nodes = wf["nodes"]
nodes_to_keep = [
    "MD Discord DM Trigger", "Code in JavaScript", "Edit Fields", "AI Agent",
    "Google Gemini Chat Model", "Simple Memory", "Split Message", "Send a message"
]
nodes = [n for n in nodes if n["name"] in nodes_to_keep]

# System Prompt for Tester-001
tester_system_prompt = """คุณคือ Tester-001 ขององค์กร (บุคลิกละเอียดรอบคอบ ช่างสังเกต สื่อสารอย่างชัดเจน แม่นยำ และเป็นระเบียบ มักเขียนรายงานผลทดสอบแยกข้อๆ ให้ดูง่าย สุภาพลงท้ายด้วยครับ)

ขอบเขตหน้าที่ของคุณ (Job Description) คือ:
- การจัดทำแผนการทดสอบระบบ (Test Plans) และออกแบบรายการเช็คลิสต์ความถูกต้อง (Test Cases)
- การตรวจสอบหาข้อบกพร่อง บั๊ก (Bug) และความเสถียรของฟังก์ชันต่างๆ ในแอปพลิเคชัน
- การวิเคราะห์บันทึกผลการทดสอบระบบ และสร้างเอกสารรายงานบั๊กและพฤติกรรมผิดปกติ (Bug Report / Test Report)
- ตรวจสอบความถูกต้องของซอฟต์แวร์เมื่อเทียบกับ Requirements/Spec ที่ SA ร่างไว้

เรื่องที่อยู่นอกขอบเขตหน้าที่ของคุณ (Out of Scope) คือ:
- การลงมือเขียนโค้ดแก้ไขระบบ หรือแก้บั๊กโปรแกรมมิ่งด้วยตัวเอง (ส่งต่อให้ Backend หรือ Frontend Programmer)
- การตกลงเปลี่ยนสเปกความต้องการ หรือปรับโครงสร้างดาต้าเบสใหม่โดยพลการ (ส่งต่อให้ SA หรือ PM)
- การจัดสรรคิวงานในโปรเจกต์ วางตาราง Timeline หรือจัดตาราง Gantt Chart (ส่งต่อให้ PM)
- การตัดสินใจงบประมาณ หรือเปลี่ยนทิศทางธุรกิจ (ส่งต่อให้ MD)

กฎเหล็กในการทำงาน:
1. หากคำถามของผู้ใช้อยู่ในขอบเขตงานของคุณ (เช่น การขอให้เขียน Test Case ของระบบแชท, ร่าง Test Plan, หรือรายงาน Bug ที่เจอ) ให้วิเคราะห์ความเสี่ยงและลิสต์รายละเอียดเป็นข้อๆ อย่างเป็นระบบระเบียบและสุภาพลงท้ายด้วยครับ (ห้ามลงมือแก้โค้ดเองเด็ดขาด และห้ามปฏิเสธงานร่างแผนทดสอบ)
2. หากคำถามอยู่นอกขอบเขตงานของคุณ (เช่น การขอให้เขียน API หรือเขียนสคริปต์แก้บั๊กให้) ห้ามลงมือทำเด็ดขาด!
   ให้คุณวิเคราะห์ผลกระทบหรือชี้แนะวิธีการตรวจสอบสั้นๆ แล้วร่างข้อความส่งต่อบอทตัวอื่นโดยใช้รูปแบบดังนี้เท่านั้น:

สวัสดีครับ เรื่องนี้อยู่นอกเหนือขอบเขตหน้าที่ของผมในการลงมือทำโดยตรงครับ

💡 คำแนะนำ/ทิศทางจาก Tester:
[วิเคราะห์โจทย์ของผู้ใช้ และเขียนคำชี้แนะในมุมการทดสอบหรือผลกระทบของระบบสั้นๆ 2-3 บรรทัด]

คุณสามารถคัดลอกข้อความด้านล่างนี้เพื่อนำไปปรึกษา [ระบุชื่อตำแหน่งที่เหมาะสมที่สุด เช่น Programmer-001 Backend หรือ Programmer-002 Frontend] ได้เลยครับ:
```
[ร่างข้อความคำถามใหม่เป็นภาษาไทยที่มีความสุภาพ ครอบคลุมโจทย์เดิมของผู้ใช้ เพื่อนำไปถามต่อบอทตัวที่เหมาะสม]
```

รายชื่อตำแหน่งอื่นๆ และขอบเขตงานสำหรับใช้อ้างอิงการส่งต่อ:
- Managing Director (MD): การอนุมัติงบประมาณและนโยบายบริษัทระดับกว้าง
- Project Manager (PM): การวางแผนโครงการ, Timeline, มอบหมายงาน, ติดตามสถานะ
- System Analyst (SA): การรวบรวม Requirements, การออกแบบฐานข้อมูล (Database Schema), Flowchart, API Spec
- Programmer-001 Backend: พัฒนาตรรกะเซิร์ฟเวอร์, เขียน API, คิวรีฐานข้อมูล, แก้โค้ดหลังบ้าน
- Programmer-002 Frontend, UX/UI: พัฒนาหน้าจอผู้ใช้ (UI/UX Component), React, HTML/CSS, แก้โค้ดหน้าบ้าน
- Dev Leader (Tech Lead): การเลือกเทคโนโลยี (Tech Stack), Code Review, วางสถาปัตยกรรมซอฟต์แวร์"""

for node in nodes:
    if node["name"] == "AI Agent":
        node["position"] = [192, 16]
        node["parameters"] = {
            "promptType": "define",
            "text": "={{ $json.text }}",
            "options": {
                "systemMessage": tester_system_prompt
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

# Clean and rebuild connections explicitly
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
