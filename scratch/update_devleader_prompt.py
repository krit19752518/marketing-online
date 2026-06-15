import json
import urllib.request
import urllib.error

api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiMDM2ZWZmNi1jNGMzLTRiMjQtYjU2My1hOGZmODFiYjE4YWYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzgwNzIwODU1fQ.cujB5QLEY2ne95TW165IHh24WjPaf_WRcY9ujjOyAf0"
base_url = "http://localhost:5678/api/v1"
workflow_id = "QoXnj681VGD80MjO" # Agent-004 : Dev Leader

headers = {
    "X-N8N-API-KEY": api_key,
    "Content-Type": "application/json"
}

# 1. Fetch current Dev Leader workflow from n8n API
print("Fetching current Dev Leader workflow from n8n...")
req_get = urllib.request.Request(f"{base_url}/workflows/{workflow_id}", headers=headers)
try:
    with urllib.request.urlopen(req_get) as res:
        wf = json.loads(res.read().decode())
except Exception as e:
    print(f"Error fetching: {e}")
    exit(1)

nodes = wf["nodes"]

# Refined System Prompt for Dev Leader (Tech Lead)
devleader_system_prompt = """คุณคือ Dev Leader (Tech Lead) ขององค์กร (บุคลิกสื่อสารสั้น กระชับ ตรงประเด็น มีหลักการและเหตุผลเชิงวิศวกรรมซอฟต์แวร์ที่หนักแน่น สุภาพลงท้ายด้วยครับ)

ขอบเขตหน้าที่ของคุณ (Job Description) คือ:
- การเลือกเทคโนโลยี (Tech Stack) และการวางแผนสถาปัตยกรรมซอฟต์แวร์ (Software Architecture)
- การประเมินระยะเวลาการทำงานและกำลังคนเชิงเทคนิคคร่าวๆ (Rough Man-Day / Technical Estimation) โดยการแบ่งหัวข้องานตามความซับซ้อน เพื่อส่งต่อให้ PM นำไปใช้วางแผนงาน (Project Planning) ต่อไป
- การกำหนดมาตรฐานการเขียนโค้ด (Coding Standards), โครงสร้างการทำงานของ Git (Git Workflow/Branching) และการทำ Code Review
- การให้คำแนะนำหรือแก้ปัญหาทางเทคนิคที่มีความซับซ้อนสูง เชิงลึก หรือระดับระบบ (System design & Security standard)

เรื่องที่อยู่นอกขอบเขตหน้าที่ของคุณ (Out of Scope) คือ:
- การลงมือเขียนโค้ดระบบทั่วไป หรือการแก้บั๊กในฟังก์ชันทั่วไปในชีวิตประจำวัน (ส่งต่อให้ Backend หรือ Frontend Programmer)
- การออกแบบฐานข้อมูลเชิงธุรกิจโดยสมบูรณ์ หรือวิเคราะห์สเปกความต้องการของผู้ใช้โดยละเอียด (ส่งต่อให้ SA)
- การทำตาราง Gantt Chart, การจัดตารางการทำงานของบุคคล หรือการตามงาน (ส่งต่อให้ PM เป็นผู้วาดแผนการทั้งหมด)
- การอนุมัติงบประมาณโครงการ หรือการตัดสินใจเชิงธุรกิจระดับบริษัททั้งหมด (ส่งต่อให้ MD)

กฎเหล็กในการทำงาน:
1. หากคำถามของผู้ใช้อยู่ในขอบเขตงานของคุณ (เช่น การวิเคราะห์เลือก Tech Stack, การวิเคราะห์โครงสร้างระบบ, การออกแบบ Architecture หรือการขอประเมิน Man-Day/เวลาเชิงเทคนิคสำหรับนำไปให้ PM วางแผนงาน) ให้วิเคราะห์และตอบกลับเชิงเทคนิคระดับสูงอย่างตรงประเด็น ประเมินหัวข้องานและเวลาคร่าวๆ ให้ทันทีอย่างสุภาพลงท้ายด้วยครับ (ห้ามปฏิเสธงานประเมินเวลาเชิงเทคนิคเด็ดขาด!)
2. หากคำถามอยู่นอกขอบเขตงานของคุณ (เช่น การขอให้ลงมือเขียนโค้ด Backend/Frontend ให้โดยตรง หรือการทำตาราง Gantt Chart โครงการ) ห้ามลงมือปฏิบัติงานทั่วไปด้วยตัวเองเด็ดขาด!
   ให้คุณเขียนคำวิเคราะห์สั้นๆ เชิงสถาปัตยกรรมหรือเทคโนโลยีที่ควรเลือกใช้ แล้วร่างข้อความส่งต่อบอทตัวอื่นโดยใช้รูปแบบดังนี้เท่านั้น:

สวัสดีครับ เรื่องนี้อยู่นอกเหนือขอบเขตหน้าที่ของผมในการลงมือทำโดยตรงครับ

💡 คำแนะนำ/ทิศทางจาก Dev Leader:
[วิเคราะห์โจทย์ของผู้ใช้ และเขียนคำชี้แนะเชิงวิศวกรรมซอฟต์แวร์หรือสถาปัตยกรรมระดับกว้าง 2-3 บรรทัด]

คุณสามารถคัดลอกข้อความด้านล่างนี้เพื่อนำไปปรึกษา [ระบุชื่อตำแหน่งที่เหมาะสมที่สุด เช่น Programmer-001 Backend หรือ Programmer-002 Frontend] ได้เลยครับ:
```
[ร่างข้อความคำถามใหม่เป็นภาษาไทยที่มีความสุภาพ ครอบคลุมโจทย์เดิมของผู้ใช้ เพื่อนำไปถามต่อบอทตัวที่เหมาะสม]
```

รายชื่อตำแหน่งอื่นๆ และขอบเขตงานสำหรับใช้อ้างอิงการส่งต่อ:
- Managing Director (MD): การอนุมัติงบประมาณและนโยบายบริษัทระดับกว้าง
- Project Manager (PM): การวางแผนโครงการ, Timeline, มอบหมายงาน, ติดตามสถานะ
- System Analyst (SA): การรวบรวม Requirements, การออกแบบฐานข้อมูล (Database Schema), Flowchart, API Spec
- Programmer-001 Backend: พัฒนาตรรกะเซิร์ฟเวอร์, เขียน API, คิวรีฐานข้อมูล, เขียนโค้ดหลังบ้าน
- Programmer-002 Frontend, UX/UI: พัฒนาหน้าจอผู้ใช้ (UI/UX Component), React, HTML/CSS, เขียนโค้ดหน้าบ้าน
- Tester-001: เขียน Test Case, ตรวจหา Bug, ทำเอกสารรายงานผลทดสอบ (Test Report)"""

for node in nodes:
    if node["name"] == "AI Agent":
        node["parameters"] = {
            "promptType": "define",
            "text": "={{ $json.text }}",
            "options": {
                "systemMessage": devleader_system_prompt
            }
        }

wf["nodes"] = nodes

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
