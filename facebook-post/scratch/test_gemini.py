import urllib.request
import json

api_key = "AIzaSyBNb6oiwC_hmECeGq1JegH6qJm4SyWR9MU"
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

req = urllib.request.Request(url)
try:
    print("Listing models...")
    with urllib.request.urlopen(req) as res:
        res_body = json.loads(res.read().decode('utf-8'))
        for m in res_body.get('models', []):
            print(f"- {m['name']} (supported methods: {m.get('supportedGenerationMethods')})")
except Exception as e:
    print("Error listing models:", e)
    if hasattr(e, 'read'):
        print("Error content:", e.read().decode('utf-8'))
