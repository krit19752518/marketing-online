import json

with open("/home/krit/my-office/scratch/decrypted_creds.json", "r") as f:
    creds = json.load(f)

for c in creds:
    if c.get("type") == "discordBotTriggerApi":
        data = c.get("data", {})
        if "allowedHttpRequestDomains" in data:
            print(f"Removing allowedHttpRequestDomains from credential {c.get('name')}")
            del data["allowedHttpRequestDomains"]

with open("/home/krit/my-office/scratch/decrypted_creds_fixed.json", "w") as f:
    json.dump(creds, f, indent=2)

print("Saved to decrypted_creds_fixed.json")
