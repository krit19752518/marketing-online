import urllib.request
import json

url = "http://127.0.0.1:5000/cards/44900790127/compose-tiktok"
payload = {
    "slide1_text": "ลดกลิ่นกายสุดคลาสสิก",
    "slide2_text": "ราคาดิ่งลึกที่สุดในรอบปี!\nจ่ายเพียง 219.- (จากราคาปกติ 599.-)",
    "slide3_text": "คลิกดูโปรโมชั่น [ลิงก์หน้าโปรไฟล์]"
}

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')

try:
    with urllib.request.urlopen(req) as response:
        res_body = response.read().decode('utf-8')
        print("Response Code:", response.status)
        print("Response Body:")
        print(json.dumps(json.loads(res_body), indent=2, ensure_ascii=False))
except Exception as e:
    print("Error calling endpoint:", e)
    if hasattr(e, 'read'):
        print(e.read().decode('utf-8'))
