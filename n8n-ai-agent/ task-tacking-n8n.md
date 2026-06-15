# Task Tracking: Discord AI Agent with n8n

## 👨‍💻 งานที่มนุษย์ต้องทำ (Human Tasks)
- [ ] **Task 1: สร้างแอปพลิเคชันและ Bot ใน Discord Developer Portal**
  - ไปที่เว็บ Discord Developer Portal แล้วสร้าง New Application (เช่น Godza GPT) [1, 2]
  - ไปที่เมนู Bot แล้วเปิดใช้งาน (Tick) `Privileged Gateway Intents` ทั้ง 3 ข้อ และกด Save [2]
  - คัดลอก `Bot Token` เก็บไว้ (ต้องกด Reset Token เพื่อคัดลอก) [3]
- [ ] **Task 2: เชิญ Bot เข้า Server Discord ของเรา**
  - ไปที่เมนู OAuth2 -> URL Generator เลือก Scope เป็น `bot` และสิทธิ์เป็น `Administrator` [3, 4]
  - คัดลอก URL ที่ได้ไปเปิดในเบราว์เซอร์ เพื่อกด Authorize ดึง Bot เข้า Server ของเรา [4]
- [ ] **Task 3: เตรียม API Keys ที่จำเป็นสำหรับการเชื่อมต่อ**
  - **n8n API Key:** ไปที่ตั้งค่าของ n8n -> n8n API -> Create API Key [4]
  - **Gemini API Key:** ไปที่ Google Gemini API กด Get API Key และสร้างโปรเจกต์เพื่อคัดลอก Key มาเก็บไว้ [5, 6]
- [ ] **Task 4: ติดตั้ง Community Node ใน n8n**
  - คัดลอกชื่อแพ็กเกจ Discord Trigger (จากใต้คลิป) ไปติดตั้งที่ Settings -> Community Nodes ใน n8n แล้วกด Install [2, 7]
- [ ] **Task 5: ตั้งค่า Workflow และ Credentials ในหน้า UI ของ n8n**
  - นำ Workflow JSON ที่ AI สร้างให้ไป Import ลงใน n8n
  - สร้างและกรอก Credentials สำหรับ **Discord Trigger** (ใช้ Client ID, Bot Token, n8n API Key และ Base URL ของ n8n ตามด้วย `api/v1`) [4, 8]
  - สร้างและกรอก Credentials สำหรับ **Gemini API** [6]
  - สร้างและกรอก Credentials สำหรับ **Discord Node** (ใช้ Bot Token) [6, 9]

## 🤖 งานที่ AI ต้องทำ (AI/Agent Tasks)
- [ ] **Task 6: สร้างโปรเจกต์ Node.js สำหรับรัน Bot Server เบื้องต้น**
  - สร้างโฟลเดอร์โปรเจกต์ (เช่น `Discord Bot`) และรันคำสั่ง `npm install discord.js` [7]
  - เขียนไฟล์ `index.js` ตาม Docs ของ Discord.js เพื่อให้ Bot สามารถ Login และออนไลน์ได้ [3, 7]
- [ ] **Task 7: เขียนโค้ด JavaScript สำหรับ Code Node ใน n8n**
  - เขียนสคริปต์เพื่อสกัดเอาเฉพาะ "ข้อความ (Text/Content)" จาก Payload ที่ Discord Trigger ส่งมา เพื่อส่งต่อให้ AI Agent [5, 8]
- [ ] **Task 8: ร่างโครงสร้าง n8n Workflow (JSON)**
  - สร้าง Workflow JSON Template ที่ประกอบด้วย: Discord Trigger -> Code Node (JavaScript) -> AI Agent (ต่อกับ Gemini Model และ Window Buffer Memory) -> Discord Node (Send Message) [5, 6, 8, 9]

