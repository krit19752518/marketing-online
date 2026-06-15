import time
import requests

url = "http://localhost:5678/webhook-test/agent-001/chat"
payload = {
    "session_id": "test_session_001",
    "message": "สวัสดีครับ แนะนำระบบจองคิวร้านตัดผมออนไลน์"
}

print("=== Starting test webhook ping loop (30 seconds) ===")
print("Please click 'Listen for test event' in n8n now!")

for i in range(30):
    try:
        response = requests.post(url, json=payload, timeout=2)
        print(f"[{i+1}/30] Sent request. Response Status: {response.status_code}")
        if response.status_code == 200:
            print("=== SUCCESS! Webhook caught the request! ===")
            print("Response Data:", response.text)
            break
    except Exception as e:
        print(f"[{i+1}/30] Connection failed: {e}")
    time.sleep(1)

print("=== Ping loop finished ===")
