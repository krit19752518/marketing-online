import sys
import os
# Add root path to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from chatbot_service import search_products, build_carousel_payload

def test_search_and_payload():
    print("Testing Keyword Search for 'polo'...")
    items = search_products(keyword="polo")
    print(f"Found {len(items)} items matching 'polo'")
    
    payload = build_carousel_payload("TEST_USER_PSID", items)
    print("Generated Carousel Payload structure:")
    import json
    print(json.dumps(payload, indent=2, ensure_ascii=False)[:1000] + "...\n")
    
    print("Testing Campaign Search for 'GRADE AAA'...")
    aaa_items = search_products(campaign="GRADE AAA")
    print(f"Found {len(aaa_items)} items for 'GRADE AAA'")
    
    aaa_payload = build_carousel_payload("TEST_USER_PSID", aaa_items)
    print("First element in GRADE AAA carousel:")
    if aaa_items:
        print(json.dumps(aaa_payload['message']['attachment']['payload']['elements'][0], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_search_and_payload()
