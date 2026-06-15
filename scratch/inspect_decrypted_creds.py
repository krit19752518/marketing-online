import json

with open("/home/krit/my-office/scratch/decrypted_creds.json", "r") as f:
    creds = json.load(f)

for c in creds:
    name = c.get("name")
    c_type = c.get("type")
    c_id = c.get("id")
    
    if "discord" in c_type.lower():
        print(f"Name: {name} (ID: {c_id}, Type: {c_type})")
        data = c.get("data", {})
        # Hide actual tokens but print keys and value lengths
        for k, v in data.items():
            val_str = str(v)
            print(f"  {k}: length={len(val_str)}, prefix={val_str[:10]}...")
        print()
