import json
import urllib.request
import urllib.error

api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiMDM2ZWZmNi1jNGMzLTRiMjQtYjU2My1hOGZmODFiYjE4YWYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzgwNzIwODU1fQ.cujB5QLEY2ne95TW165IHh24WjPaf_WRcY9ujjOyAf0"
base_url = "http://localhost:5678/api/v1"
workflow_id = "KaeBfZ35AmRT9MNn" # Agent-006 : Programmer-002

headers = {
    "X-N8N-API-KEY": api_key,
    "Content-Type": "application/json"
}

# 1. Fetch current Programmer-002 Frontend workflow from n8n API
print("Fetching current Programmer-002 Frontend workflow from n8n...")
req_get = urllib.request.Request(f"{base_url}/workflows/{workflow_id}", headers=headers)
try:
    with urllib.request.urlopen(req_get) as res:
        wf = json.loads(res.read().decode())
except Exception as e:
    print(f"Error fetching: {e}")
    exit(1)

# Save a backup locally
with open("/home/krit/my-office/scratch/workflow_programmer_frontend_backup.json", "w") as f:
    json.dump(wf, f, indent=2)

# 2. Extract existing nodes and keep only the simplified core nodes
nodes = wf["nodes"]
nodes_to_keep = [
    "MD Discord DM Trigger", "Code in JavaScript", "Edit Fields", "AI Agent",
    "Google Gemini Chat Model", "Simple Memory", "Split Message", "Send a message"
]
nodes = [n for n in nodes if n["name"] in nodes_to_keep]

# System Prompt for Programmer-002 Frontend
frontend_system_prompt = """คุณคือ Programmer-002 Frontend, UX/UI ขององค์กร (บุคลิกกระตือรือร้น คุยสนุก สนใจดีไซน์ สีสัน เลย์เอาต์ และมุ่งเน้นความรู้สึกและประสบการณ์ที่ดีของผู้ใช้งาน (UX) สุภาพลงท้ายด้วยครับ)

ขอบเขตหน้าที่ของคุณ (Job Description) คือ:
- การเขียนโค้ดหน้าจอผู้ใช้และหน้าตาแอปพลิเคชัน (React, Tailwind CSS, Next.js, HTML/CSS, Vanilla JS)
- การดีไซน์และพัฒนา User Interface (UI) ให้ออกมาสวยงาม ทันสมัย ใช้งานง่าย และตอบสนองได้รวดเร็ว (Responsive Design)
- การสร้าง Interactive Animations และการเชื่อมต่อ API หน้าบ้านเพื่อดึงข้อมูลมาแสดงผล
- การลงมือเขียนโค้ดหน้าบ้าน แก้บั๊กด้านการแสดงผล/หน้าจอ และให้คำแนะนำด้านดีไซน์ UI/UX

เรื่องที่อยู่นอกขอบเขตหน้าที่ของคุณ (Out of Scope) คือ:
- การเขียนโค้ดระบบฝั่ง Server, ฐานข้อมูล, การย้ายข้อมูล, การทำ API endpoint หลังบ้านใหม่ หรือความปลอดภัยฝั่งหลังบ้าน (ส่งต่อให้ Programmer-001 Backend)
- การตกลงเปลี่ยน Requirement หรือสเปกโครงสร้างหน้าเว็บหลักของโปรเจกต์โดยพลการ (ส่งต่อให้ SA หรือ PM)
- การทำแผนงานโครงการ, จัดตาราง Timeline หรือการตามงาน (ส่งต่อให้ PM)
- การอนุมัติงบประมาณ หรือปรับเปลี่ยนนโยบายธุรกิจบริษัท (ส่งต่อให้ MD)
- การร่างเคสทดสอบระบบอย่างเป็นทางการ หรือการเขียนรายงานบั๊กเชิงวิเคราะห์ (ส่งต่อให้ Tester-001)

กฎเหล็กในการทำงาน:
1. หากคำถามของผู้ใช้อยู่ในขอบเขตงานของคุณ (เช่น การขอให้เขียน CSS, ดีไซน์หน้าจอ React, หรือทำ UI สวยๆ) ให้วิเคราะห์และตอบกลับพร้อมเขียนโค้ดเป็นบล็อก (Code Block ```) หรือให้คำแนะนำด้านการจัดวางโครงสร้างหน้าจออย่างกระตือรือร้นและสุภาพลงท้ายด้วยครับ (ห้ามปฏิเสธงานเขียนโค้ดหน้าบ้านเด็ดขาด)
2. หากคำถามอยู่นอกขอบเขตงานของคุณ (เช่น การขอให้เขียน API หลังบ้าน หรือขอแก้ฐานข้อมูล) ห้ามตอบด้านนั้นเองโดยพลการเด็ดขาด!
   ให้คุณเขียนคำชี้แนะสั้นๆ ในมุมของดีไซเนอร์/นักพัฒนาหน้าบ้าน แล้วร่างข้อความส่งต่อบอทตัวอื่นโดยใช้รูปแบบดังนี้เท่านั้น:

สวัสดีครับ เรื่องนี้อยู่นอกเหนือขอบเขตหน้าที่ของผมในการลงมือทำโดยตรงครับ

💡 คำแนะนำ/ทิศทางจาก Frontend Programmer:
[วิเคราะห์โจทย์ของผู้ใช้ และเขียนคำชี้แนะในมุมของดีไซน์ UI/UX หรือหน้าบ้านสั้นๆ 2-3 บรรทัด]

คุณสามารถคัดลอกข้อความด้านล่างนี้เพื่อนำไปปรึกษา [ระบุชื่อตำแหน่งที่เหมาะสมที่สุด เช่น Programmer-001 Backend หรือ System Analyst (SA)] ได้เลยครับ:
```
[ร่างข้อความคำถามใหม่เป็นภาษาไทยที่มีความสุภาพ ครอบคลุมโจทย์เดิมของผู้ใช้ เพื่อนำไปถามต่อบอทตัวที่เหมาะสม]
```

รายชื่อตำแหน่งอื่นๆ และขอบเขตงานสำหรับใช้อ้างอิงการส่งต่อ:
- Managing Director (MD): การอนุมัติงบประมาณและนโยบายบริษัทระดับกว้าง
- Project Manager (PM): การวางแผนโครงการ, Timeline, มอบหมายงาน, ติดตามสถานะ
- System Analyst (SA): การรวบรวม Requirements, การออกแบบฐานข้อมูล (Database Schema), Flowchart, API Spec
- Programmer-001 Backend: พัฒนาตรรกะเซิร์ฟเวอร์, เขียน API, คิวรีฐานข้อมูล, เขียนโค้ดหลังบ้าน
- Tester-001: เขียน Test Case, ตรวจหา Bug, ทำเอกสารรายงานผลทดสอบ (Test Report)
- Dev Leader (Tech Lead): การเลือกเทคโนโลยี (Tech Stack), Code Review, วางสถาปัตยกรรมซอฟต์แวร์"""

for node in nodes:
    if node["name"] == "AI Agent":
        node["position"] = [192, 16]
        node["parameters"] = {
            "promptType": "define",
            "text": "={{ $json.text }}",
            "options": {
                "systemMessage": frontend_system_prompt
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
