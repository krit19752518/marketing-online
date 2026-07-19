import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.hermes_service import HermesService

def test_filter_inbound_prompt():
    raw_message = "นี่มึง ไปดูยอดขายให้กูหน่อยดิ"
    cleaned = HermesService.filter_inbound_prompt(raw_message)
    assert "มึง" not in cleaned
    assert "กู" not in cleaned
    assert "เธอ" in cleaned or "เรา" in cleaned

def test_enrich_system_prompt():
    prompt = HermesService.enrich_system_prompt("schema detail")
    assert "RayKha" in prompt
    assert "schema detail" in prompt

def test_filter_outbound_response():
    ai_msg = "ได้เลยค่าาาา ยินดีต้อนรับบอสมากกกกค่ะะะ"
    cleaned = HermesService.filter_outbound_response(ai_msg)
    # Repeating characters should be reduced
    assert "ค่าาาา" not in cleaned
    assert "มากกกก" not in cleaned
    assert "ค่ะะะ" not in cleaned

if __name__ == "__main__":
    test_filter_inbound_prompt()
    test_enrich_system_prompt()
    test_filter_outbound_response()
    print("All HermesService unit tests passed successfully!")
