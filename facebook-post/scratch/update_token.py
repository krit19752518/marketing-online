import os
import requests
from dotenv import load_dotenv

load_dotenv()

# User input Token and Page ID
USER_TOKEN = "EAATOJVpASlwBRmsWqUzMYUGZBZALRZBUccDY1nsiIGUd5rIy2nN7ZBtZAh2tWPNa31wIMF4GlKenRvZCb8MZC9UFRiw2oc1sdZABxyaORx1Dq6gT7hQeNv5CfrF21VLjsOAnoZCTwinH0TwLkjSzZCDN9rQChn74JCQmnYFBzWL4rqhEQENqM2UtFZBHgWInaWBiMDpdZBv3weL49e3aziwPb0BuIDKUw5WlD0KPZBQZDZD"
PAGE_ID = "1181871538339079"
APP_ID = "1352559730117212"

# 1. Exchange for Long-Lived Access Token
print("1. Exchanging for Long-Lived User Access Token...")
# We retrieve the app secret from .env if available, or fetch it via graph explorer values.
# If no secret is stored, we will directly call me/accounts.
url = f"https://graph.facebook.com/v25.0/me/accounts?access_token={USER_TOKEN}"
res = requests.get(url)
data = res.json()

if "error" in data:
    print(f"Error calling FB API: {data['error']['message']}")
    exit(1)

# Find the specific page token
page_token = None
for page in data.get("data", []):
    if page.get("id") == PAGE_ID:
        page_token = page.get("access_token")
        print(f"Success! Found token for page: {page.get('name')}")
        break

if page_token:
    # Read current env
    env_lines = []
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            env_lines = f.readlines()
            
    # Re-write .env
    new_lines = []
    has_page_id = False
    has_page_token = False
    
    for line in env_lines:
        if line.startswith("FB_PAGE_ID="):
            new_lines.append(f"FB_PAGE_ID={PAGE_ID}\n")
            has_page_id = True
        elif line.startswith("FB_PAGE_ACCESS_TOKEN="):
            new_lines.append(f"FB_PAGE_ACCESS_TOKEN={page_token}\n")
            has_page_token = True
        else:
            new_lines.append(line)
            
    if not has_page_id:
        new_lines.append(f"FB_PAGE_ID={PAGE_ID}\n")
    if not has_page_token:
        new_lines.append(f"FB_PAGE_ACCESS_TOKEN={page_token}\n")
        
    with open(".env", "w", encoding="utf-8") as f:
        f.writelines(new_lines)
        
    print("Successfully updated .env file with the new Page Access Token!")
else:
    print(f"Could not find page with ID {PAGE_ID} in this token's authorized list.")
