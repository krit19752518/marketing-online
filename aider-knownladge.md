# โครงสร้างเนื้อหาภายในไฟล์ aider-knowledge.md ที่ถูกสร้างขึ้น
"""
# Aider Knowledge Base & Architecture Guide

Aider เป็นเครื่องมือประเภท AI Pair Programming ในรูปแบบ Command Line Interface (CLI) ที่ทำงานประสานร่วมกับ Local Git Repository ของคุณโดยตรง เพื่อทำการอ่าน แก้ไข และทดสอบโค้ดโดยอัตโนมัติ

## 1. การสถาปัตยกรรมและการเชื่อมต่อกับ Ollama (Local LLM)
Aider สามารถแปลงคำสั่งของผู้ใช้และส่งต่อไปยัง OpenAI-compatible API Gateway ซึ่งรวมถึง Ollama ที่รันอยู่ในเครื่องของคุณ (พอร์ตมาตรฐาน: `http://localhost:11434`)

### โมเดลแนะนำสำหรับการเขียนโค้ดภายในเครื่อง (Local Coding Models)
- **qwen2.5-coder** (แนะนำที่สุด มีขนาด 1.5B, 7B, 14B, 32B) - เข้าใจไวยากรณ์และโครงสร้างภาษาได้ดีเยี่ยม Context Window กว้าง
- **deepseek-coder** (ขนาด 6.7B) - โดดเด่นเรื่องการทำ Logical Reasoning และอัลกอริทึม
- **codegemma** (โดย Google) - แม่นยำในกลุ่มภาษาหลัก เช่น Python, JavaScript, Java, C++

## 2. วิธีการติดตั้งที่ถูกต้องบนระบบปฏิบัติการ Linux
เนื่องจากระบบปฏิบัติการ Linux รุ่นใหม่ๆ มีการเปิดใช้งานกฎ PEP 668 เพื่อป้องกันการพังของระบบ (Externally Managed Environment) การติดตั้ง Aider จึงควรใช้วิธีแยกสภาพแวดล้อมอิสระ:

```bash
# วิธีที่ 1: ผ่าน uv (เร็วที่สุดและจัดการเวอร์ชัน Python ได้ฉลาด)
curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh
source $HOME/.local/bin/env
uv tool install --python 3.11 aider-chat

# วิธีที่ 2: ผ่าน pipx
sudo apt update && sudo apt install pipx -y
pipx ensurepath
# (ปิดแล้วเปิด Terminal ใหม่)
pipx install aider-chat --python python3.11