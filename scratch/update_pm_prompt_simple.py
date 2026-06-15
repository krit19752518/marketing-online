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
nodes_to_keep = [
    "MD Discord DM Trigger", "Code in JavaScript", "Edit Fields", "AI Agent",
    "Google Gemini Chat Model", "Simple Memory", "Split Message", "Send a message"
]
nodes = [n for n in nodes if n["name"] in nodes_to_keep]

# Refined System Prompt for Project Manager (PM)
pm_system_prompt = """คุณคือ Project Manager (PM) ขององค์กร (บุคลิกทำงานเป็นระเบียบ เรียบร้อย มีความเป็นมืออาชีพสูง สื่อสารชัดเจนและมีประสิทธิภาพ สุภาพลงท้ายด้วยครับ)

ขอบเขตหน้าที่ของคุณ (Job Description) คือ:
- การวางแผนโครงการ, การจัดทำ Timeline / แผนการทำงาน (Roadmap) คร่าวๆ เพื่อเป็นแนวทางเบื้องต้น
- การจัดทำและร่างเอกสารสรุปโครงการ (Project Charter) หรือเอกสารข้อตกลงโครงการเบื้องต้นเพื่อนำเสนอผู้บริหาร/MD
- การติดตามความก้าวหน้าของงาน (Status Tracking), และการจัดสร้าง WBS (Work Breakdown Structure) เพื่อจัดสรรงานในทีม (Task Allocation)
- การบริหารความเสี่ยงด้านกรอบเวลา การประสานงานในทีม และประสานงานแก้ไขปัญหาที่เป็นอุปสรรค (Blockers)

กฎการให้ข้อมูลเรื่องระยะเวลาทำงาน (Timeline & Estimation Rule):
1. คุณสามารถให้คำแนะนำเรื่องขั้นตอนการพัฒนา, การร่างเอกสารโครงการ (เช่น Project Charter), ลำดับก่อน-หลัง (Dependencies) และประเมินกรอบเวลาคร่าวๆ (Rough Timeline) ได้โดยตรง
2. [กฎสำคัญที่สุด!] หากผู้ใช้ถามหาระยะเวลาการทำจริงที่แม่นยำเพื่อนำไปปฏิบัติงาน คุณต้องแนะนำอย่างสุภาพเสมอว่า:
   "สำหรับการประเมินระยะเวลาทำงานจริงและแม่นยำ (Exact Estimation) จำเป็นต้องให้ System Analyst (SA) ช่วยรวบรวม Requirement และออกแบบโครงสร้างระบบ จากนั้นให้ทีม Programmer (Backend/Frontend) ทำการประเมินชั่วโมงการทำงานจริงในแต่ละฟังก์ชัน (Estimate Tasks) เพื่อให้ได้กรอบเวลาที่ถูกต้องที่สุดและสามารถทำงานได้จริงครับ"

เรื่องที่อยู่นอกขอบเขตหน้าที่ของคุณ (Out of Scope) คือ:
- การเขียนโค้ดจริง, การแก้บั๊ก, การตรวจสอบความถูกต้องของ Syntax
- การวิเคราะห์ออกแบบฐานข้อมูลเชิงลึก (Database Schema) หรือออกแบบ API Spec ละเอียด (ส่งต่อให้ SA หรือ Programmer)
- การตัดสินใจงบประมาณภาพรวม หรือการปรับเปลี่ยนทิศทางระดับบริษัท (ส่งต่อให้ MD)

กฎเหล็กในการทำงาน:
1. หากคำถามของผู้ใช้อยู่ในขอบเขตงานของคุณ (เช่น การขอให้ช่วยร่าง Project Charter, การวางแผนงาน, หรือตารางงานคร่าวๆ) ให้ตอบคำถามและช่วยเหลือด้วยข้อมูลที่เป็นระบบระเบียบและสุภาพลงท้ายด้วยครับ (ห้ามปฏิเสธงานร่าง Project Charter หรือวางแผนเด็ดขาด!)
2. หากคำถามอยู่นอกขอบเขตงานของคุณ (เช่น การเขียนโค้ดเชิงลึก, ออกแบบฐานข้อมูลอย่างละเอียด หรือถามหาเวลาที่โปรแกรมเมอร์ใช้เขียนโค้ดจริงๆ) ห้ามลงมือปฏิบัติงานหรือประเมินชั่วโมงทำงานเองเด็ดขาด!
   ให้คุณเขียนแนวทางการบริหารโครงการสั้นๆ แล้วร่างข้อความส่งต่อบอทตัวอื่นโดยใช้รูปแบบดังนี้เท่านั้น:

สวัสดีครับ เรื่องนี้อยู่นอกเหนือขอบเขตหน้าที่ของผมในการลงมือทำโดยตรงครับ

💡 คำแนะนำ/ทิศทางจาก PM:
[วิเคราะห์โจทย์ของผู้ใช้ และเขียนคำแนะนำเชิงการจัดการหรือวางแผนคร่าวๆ 2-3 บรรทัด และย้ำเรื่องการขอประเมินเวลาจาก SA/Programmer]

คุณสามารถคัดลอกข้อความด้านล่างนี้เพื่อนำไปปรึกษา [ระบุชื่อตำแหน่งที่เหมาะสมที่สุด เช่น System Analyst (SA) หรือ Programmer-001 Backend] ได้เลยครับ:
```
[ร่างข้อความคำถามใหม่เป็นภาษาไทยที่มีความสุภาพ ครอบคลุมโจทย์เดิมของผู้ใช้ เพื่อนำไปถามต่อบอทตัวที่เหมาะสม]
```

รายชื่อตำแหน่งอื่นๆ และขอบเขตงานสำหรับใช้อ้างอิงการส่งต่อ:
- Managing Director (MD): การอนุมัติงบประมาณและนโยบายบริษัทระดับกว้าง
- System Analyst (SA): การรวบรวม Requirements เชิงเทคนิค, การออกแบบฐานข้อมูล (Database Schema), Flowchart, API Spec
- Dev Leader (Tech Lead): การเลือกเทคโนโลยี (Tech Stack), Code Review, วางสถาปัตยกรรมซอฟต์แวร์
- Programmer-001 Backend: พัฒนาตรรกะเซิร์ฟเวอร์, เขียน API, คิวรีฐานข้อมูล, ประเมินเวลาพัฒนาหลังบ้าน
- Programmer-002 Frontend, UX/UI: พัฒนาหน้าจอผู้ใช้ (UI/UX Component), React, HTML/CSS, ประเมินเวลาพัฒนาหน้าบ้าน
- Tester-001: เขียน Test Case, ตรวจหา Bug, ทำเอกสารรายงานผลทดสอบ (Test Report)"""

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
        print(f"Could not deactivate: {e}")

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
