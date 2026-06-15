import urllib.request
import json

import os
api_key = os.environ.get("OPENROUTER_API_KEY", "")
url = "https://openrouter.ai/api/v1/models"

req = urllib.request.Request(url)
try:
    print("Listing OpenRouter models...")
    with urllib.request.urlopen(req) as res:
        res_body = json.loads(res.read().decode('utf-8'))
        # print models that have ':free' in their id
        for m in res_body.get('data', []):
            m_id = m.get('id', '')
            if ':free' in m_id:
                print(f"- {m_id} (context: {m.get('context_length')})")
except Exception as e:
    print("Error listing OpenRouter models:", e)
    if hasattr(e, 'read'):
        print("Error content:", e.read().decode('utf-8'))
