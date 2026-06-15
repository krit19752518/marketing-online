import json
import subprocess

nodes = [
  {
    "parameters": {
      "httpMethod": "POST",
      "path": "tiktok-scraper-trigger",
      "options": {}
    },
    "id": "node-1-webhook",
    "name": "Webhook",
    "type": "n8n-nodes-base.webhook",
    "typeVersion": 1,
    "position": [112, 304],
    "webhookId": "tiktok-scraper-webhook-id"
  },
  {
    "parameters": {
      "promptType": "define",
      "text": "คุณคือนักการตลาดสายป้ายยาที่มีอารมณ์ขันและจริงใจ วิเคราะห์ข้อมูลสินค้าต่อไปนี้ แล้วเขียนข้อความสำหรับภาพสไลด์ TikTok 3 หน้า:\nหน้า 1: พาดหัวดึงดูดความสนใจ (Hook) แบบสั้นๆ ไม่เกิน 10 คำ\nหน้า 2: เปรียบเทียบราคา (ราคาเก่า vs ราคาใหม่) พร้อมบอกว่าทำไมถึงคุ้ม\nหน้า 3: Call to Action ให้คนกดลิงก์หน้าโปรไฟล์\n\nนอกจากนี้ ให้เขียน Image Prompt สั้นๆ ภาษาอังกฤษ 1 ประโยค เพื่อให้ AI สร้างภาพพื้นหลังที่สื่อถึงสินค้านี้แบบ Abstract สวยๆ\n\nข้อมูลสินค้า:\nชื่อ: {{ $json.body.product_name }}\nราคาเก่า: {{ $json.body.old_price }}\nราคาใหม่: {{ $json.body.new_price }}\nลดราคา: {{ $json.body.discount_percent }}%\nURL: {{ $json.body.product_url }}"
    },
    "id": "ollama-chain",
    "name": "Ollama Chain",
    "type": "@n8n/n8n-nodes-langchain.chainLlm",
    "typeVersion": 1.4,
    "position": [512, 288]
  },
  {
    "parameters": {
      "model": "llama3.2:3b",
      "options": {}
    },
    "id": "ollama-model",
    "name": "Ollama Chat Model",
    "type": "@n8n/n8n-nodes-langchain.lmChatOllama",
    "typeVersion": 1,
    "position": [480, 500],
    "credentials": {
      "ollamaApi": {
        "id": "a2b8e3df-498c-4f7d-8be9-cf4d8ebcd96a",
        "name": "Ollama Local account"
      }
    }
  },
  {
    "parameters": {
      "method": "POST",
      "url": "https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key=AIzaSyBNb6oiwC_hmECeGq1JegH6qJm4SyWR9MU",
      "sendBody": True,
      "specifyBody": "json",
      "jsonBody": '={{ JSON.stringify({ "instances": [ { "prompt": $json.text.match(/Image Prompt:?\\\\s*([^\\\\n]*)/i)?.[1] || $json.text } ], "parameters": { "sampleCount": 1 } }) }}',
      "options": {}
    },
    "id": "node-4-gemini",
    "name": "Gemini API (Image Generation)",
    "type": "n8n-nodes-base.httpRequest",
    "typeVersion": 4.1,
    "position": [768, 288]
  },
  {
    "parameters": {
      "command": "=python3 /data/shared-media/process_images.py --image_b64 '{{ $json.predictions[0].bytesBase64Encoded }}' --text '{{ $(\"Ollama Chain\").item.json.text }}'"
    },
    "id": "node-5-python",
    "name": "Image Processing",
    "type": "n8n-nodes-base.executeCommand",
    "typeVersion": 1,
    "position": [992, 288]
  },
  {
    "parameters": {
      "chatId": "YOUR_CHAT_ID",
      "text": "=โพสต์ TikTok ใหม่พร้อมแล้ว! 🚀\n\n{{ $(\"Ollama Chain\").item.json.text }}",
      "additionalFields": {}
    },
    "id": "node-6-telegram",
    "name": "Telegram / Discord",
    "type": "n8n-nodes-base.telegram",
    "typeVersion": 1.1,
    "position": [1216, 288]
  }
]

connections = {
  "Webhook": {
    "main": [
      [
        {
          "node": "Ollama Chain",
          "type": "main",
          "index": 0
        }
      ]
    ]
  },
  "Ollama Chat Model": {
    "ai_languageModel": [
      [
        {
          "node": "Ollama Chain",
          "type": "ai_languageModel",
          "index": 0
        }
      ]
    ]
  },
  "Ollama Chain": {
    "main": [
      [
        {
          "node": "Gemini API (Image Generation)",
          "type": "main",
          "index": 0
        }
      ]
    ]
  },
  "Gemini API (Image Generation)": {
    "main": [
      [
        {
          "node": "Image Processing",
          "type": "main",
          "index": 0
        }
      ]
    ]
  },
  "Image Processing": {
    "main": [
      [
        {
          "node": "Telegram / Discord",
          "type": "main",
          "index": 0
        }
      ]
    ]
  }
}

nodes_json = json.dumps(nodes)
connections_json = json.dumps(connections)

# Escaping single quotes for SQL
nodes_escaped = nodes_json.replace("'", "''")
connections_escaped = connections_json.replace("'", "''")

sql = f"UPDATE workflow_entity SET nodes = '{nodes_escaped}', connections = '{connections_escaped}' WHERE id = 'ct8PdAzqcjrjHL4x';"

with open('/tmp/update_tiktok.sql', 'w') as f:
    f.write(sql)

subprocess.run(["docker", "exec", "-i", "content_marketing_db", "psql", "-U", "n8n_user", "-d", "content_marketing", "-f", "-"], stdin=open('/tmp/update_tiktok.sql', 'r'))
print("TikTok Flow successfully updated in DB!")
