ส่วนที่ 1: Core Commands & Architecture

    What is Claude Code: เป็น Agentic CLI tool ที่ทำงานบน Terminal โดยสามารถเข้าถึงระบบไฟล์, รันคำสั่ง Bash, ใช้งาน Git และช่วยเขียน/แก้ไขโค้ดได้โดยตรงผ่าน Agent Loop

    Primary Command Structure:

        claude : เริ่มต้นใช้งานในโฟลเดอร์ปัจจุบัน

        claude "คำสั่งออน์ไลน์" : สั่งงานแบบ One-liner (เช่น claude "fix typos in README.md")

    Slash Commands (คำสั่งภายใน Prompt):

        /dev : สั่งให้เอเจนต์เริ่มทำภารกิจพัฒนาฟีเจอร์ใหม่

        /bug : สั่งให้ออกแบบและแก้ปัญหาบั๊กที่ระบุ

        /explain : อธิบายโค้ดหรือโครงสร้างโปรเจกต์ในบริบทปัจจุบัน

        /compact : บีบอัดประวัติการสนทนา (Conversation History) เพื่อประหยัด Token และลดต้นทุน

        /history : ดูประวัติการสั่งงานย้อนหลัง

        /undo : ย้อนกลับการแก้ไขล่าสุดที่เอเจนต์ทำลงไป

        /exit หรือ /quit : ออกจากการทำงาน

ส่วนที่ 2: Workflow & Best Practices

    Git Integration: Claude Code จะทำงานได้ดีที่สุดเมื่ออยู่ใน Git Repository มันจะสร้าง Branch ใหม่ หรือ Commit งานให้โดยอัตโนมัติ (หรือขออนุญาตก่อน) ควรแนะนำให้ผู้ใช้ Commit งานตัวเองก่อนเรียกใช้ Claude Code เสมอเพื่อความปลอดภัย

    Permission Gates: เครื่องมือนี้จะมีระบบความปลอดภัยที่ต้องกดยืนยัน (Approve) ก่อนที่เอเจนต์จะรันคำสั่ง Bash ที่มีความเสี่ยง หรือทำการอ่าน/เขียนไฟล์นอกขอบเขต

    Token Management: อธิบายกลไกที่ Claude Code โหลดไฟล์เข้า Context window ถ้าโปรเจกต์ใหญ่เกินไป ควรใช้ไฟล์ .claudecodeignore หรือ .gitignore เพื่อกันไม่ให้เอเจนต์โหลดไฟล์ที่ไม่จำเป็น (เช่น node_modules, build artifacts) เข้าไปจนสเปืองโควตา Token

ส่วนที่ 3: Common Troubleshooting (การแก้ปัญหาที่พบบ่อย)

    Authentication Issues: วิธีแก้ปัญหาเมื่อ Session หลุด หรือการตั้งค่า API Key ผ่าน Environment Variable (ANTHROPIC_API_KEY)

    Infinite Loops: กรณีที่เอเจนต์ติดลูปแก้โค้ดแล้วรันเทสไม่ผ่านซ้ำ ๆ แนะนำวิธีใช้ปุ่มกดเพื่อเบรก (Ctrl+C) และเปลี่ยนคำสั่งสั่งงานใหม่ให้แคบลง

    Cost Management: วิธีดูและควบคุมค่าใช้จ่าย (Cost tracking) ที่เกิดขึ้นระหว่างเปิด Agent loop ในแต่ละงาน

ส่วนที่ 4: Linux & Full-Stack Deployment Workflow

    Process Management: ในการทำ Full-Stack, Claude Code มักจะต้องรัน Dev Server ทั้งฝั่ง Front และ Back พร้อมกัน แนะนำให้สอนให้เอเจนต์รู้จักการใช้เครื่องมือจำพวก tmux, screen หรือรัน background process (nohup command &) เพื่อไม่ให้เทอร์มินอลหลักที่รัน Claude Code ค้างหรือติดล็อก

    Port & Firewall Awareness: การทดสอบสคริปต์หรือ API บน Linux (โดยเฉพาะบน VPS) เอเจนต์ต้องระวังเรื่องการผูก Port (เช่น 3000, 8000) หากเปิดรันชนกัน จะต้องแนะนำคำสั่งเช็กพอร์ตอย่าง sudo lsof -i :port หรือ netstat และการเช็กกฎ Firewall (เช่น ufw status) เสมอ

    Environment Variables: การจัดการไฟล์ .env สำหรับ API Keys และ Config ต่างๆ ต้องระวังไม่ให้ Claude Code เผลอแก้ไขค่าคีย์สำคัญ หรือเผลอ Commit ไฟล์ความลับขึ้น Git เด็ดขาด แนะนำให้ใช้ .claudecodeignore บล็อกไฟล์ .env เสมอ

ส่วนที่ 5: AI Agent & Automation Development Patterns

    Building AI Agents via Claude Code: เมื่อสั่งให้ Claude Code เขียนหรือวางระบบ AI Agent ตัวอื่น (เช่น การเซ็ตอัพสคริปต์ Ollama, Python Agents หรือเวิร์กโฟลว์ n8n):

        ให้เน้นสถาปัตยกรรมแบบ Modular/Clean Architecture เพื่อแยกส่วนของ Prompt, Logic และ Third-party API Connections ออกจากกัน เพื่อให้ตรวจเช็กบั๊กง่าย

        Prompt Engineering Testing: เวลาให้ Claude Code เขียน Prompt ให้เอเจนต์ตัวอื่น แนะนำให้สร้างไฟล์แยก เช่น prompts.json หรือ config.py เพื่อให้แก้ไขและปรับจูน (Tuning) ได้ง่ายโดยไม่ต้องไปไล่แก้ในโค้ดหลัก

    API Hooking & Live Data Analytics: หากทำโปรเจกต์ประเภทดึงข้อมูลสด (Live Data) หรือยิง Webhook (เช่น Telegram, LINE) ต้องสอนให้เอเจนต์เขียนระบบจำพวก Error Handling, Logging และ Retry Mechanism เสมอ เพราะระบบ Automation มีโอกาสหลุดได้ง่ายหากเกิด Network Timeout

ส่วนที่ 6: Resource & Cost Control on Linux

    Resource Management: ในจังหวะที่ Claude Code ทำการรัน Build หรือทดสอบสคริปต์หนักๆ บน Linux Server อาจกิน CPU/RAM สูง แนะนำให้เปิดใช้งานคิวอ้างอิงสำหรับการเช็กสเปซและการทำงานของ Memory (เช่น df -h, free -m, top)

    Context Limit Alert: การเขียน AI Agent มักจะเกี่ยวข้องกับ Library และ Dependencies จำนวนมาก ต้องย้ำเตือนให้เอเจนต์เขียนกติกาข้าม (Ignore) โฟลเดอร์จำพวก node_modules, venv, .git หรือไฟล์ Database (เช่น .db, .sqlite) เพื่อไม่ให้หนัก Context Window