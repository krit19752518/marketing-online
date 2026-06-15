import time
import urllib.request
import json

def test_generation():
    prompt = """คุณคือเซียนหุ้นข้างบ้านที่ชอบวิเคราะห์ราคาสินค้าของใช้ทั่วไปแบบปั่นๆ ฮาๆ
ช่วยเขียนประโยคแนะนำ/วิเคราะห์สินค้าสั้นๆ แค่ 1 ประโยค (ย้ำ: ความยาวห้ามเกิน 1 ประโยคเด็ดขาด และห้ามยาวเกิน 25 คำ) โดยให้เข้ากับสินค้า 'น้ำยาซักผ้า เดียร์นี่ กลิ่น ลัชบลูม ขนาด 500 มล.' ที่ลดราคาถึง 87%
ใช้คำศัพท์แนวเทรดหุ้นปั่นๆ ผสมภาษาชาวบ้าน เช่น "กราฟหลุดแนวรับแล้ว ราคานี้ต้องช้อน", "ราคาดิ่งเหวแบบนี้รีบสอยด่วน" เป็นต้น
ห้ามเกริ่นนำ ห้ามทวนชื่อสินค้าหรือเขียนราคาตัวเลข ซ้ำซ้อน ห้ามใส่แฮชแท็ก ห้ามมีเครื่องหมายคำพูด ตอบสั้นๆ แค่ประโยคนั้นตรงๆ เลย"""

    url = "http://localhost:11434/api/generate"
    headers = {"Content-Type": "application/json"}
    body = {
        "model": "llama3.2:3b",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.85,
            "num_predict": 50
        }
    }
    
    req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers=headers)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            res_body = json.loads(res.read().decode('utf-8'))
            ollama_res = res_body.get('response', '').strip()
            print(f"Time taken: {time.time() - t0:.2f}s")
            print("Response:", repr(ollama_res))
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    for i in range(3):
        print(f"--- Run {i+1} ---")
        test_generation()
