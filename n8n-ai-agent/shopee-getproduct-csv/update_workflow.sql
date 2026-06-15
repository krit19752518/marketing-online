UPDATE workflow_entity 
SET 
  nodes = '[
    {
      "parameters": {},
      "id": "e6a2b8e3-0d33-4bb3-ae62-0db35fa2a8e1",
      "name": "On clicking ''Execute''",
      "type": "n8n-nodes-base.manualTrigger",
      "typeVersion": 1,
      "position": [100, 200]
    },
    {
      "parameters": {
        "command": "python3 -u /data/shared-media/shopee/filter_csv.py | tee /proc/1/fd/1"
      },
      "id": "e6a2b8e3-0d33-4bb3-ae62-0db35fa2a8e2",
      "name": "Filter Shopee CSV",
      "type": "n8n-nodes-base.executeCommand",
      "typeVersion": 1,
      "position": [300, 200]
    },
    {
      "parameters": {
        "command": "node /data/shared-media/shopee/import_to_db.js | tee /proc/1/fd/1"
      },
      "id": "e6a2b8e3-0d33-4bb3-ae62-0db35fa2a8e3",
      "name": "Bulk Copy to DB",
      "type": "n8n-nodes-base.executeCommand",
      "typeVersion": 1,
      "position": [550, 200]
    },
    {
      "parameters": {
        "path": "shopee-progress",
        "responseMode": "lastNode",
        "options": {}
      },
      "id": "e6a2b8e3-0d33-4bb3-ae62-0db35fa2a8e4",
      "name": "Webhook Trigger",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [100, 450],
      "webhookId": "88981df5-0d6f-45cf-a0e2-a7a53696f8c2"
    },
    {
      "parameters": {
        "command": "cat /data/shared-media/shopee/progress.txt 2>/dev/null || echo ''No execution in progress yet.''"
      },
      "id": "e6a2b8e3-0d33-4bb3-ae62-0db35fa2a8e5",
      "name": "Read Progress File",
      "type": "n8n-nodes-base.executeCommand",
      "typeVersion": 1,
      "position": [300, 450]
    }
  ]'::json,
  connections = '{
    "On clicking ''Execute''": {
      "main": [
        [
          {
            "node": "Filter Shopee CSV",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Filter Shopee CSV": {
      "main": [
        [
          {
            "node": "Bulk Copy to DB",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Webhook Trigger": {
      "main": [
        [
          {
            "node": "Read Progress File",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }'::json,
  settings = '{"executionOrder": "v1"}'::json
WHERE id = 'QoByMxliB4ZmD2Hc';
