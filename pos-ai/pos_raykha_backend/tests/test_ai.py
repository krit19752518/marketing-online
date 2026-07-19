import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.ai_service import AIService

def test_safe_select_query():
    # Valid SELECT queries
    assert AIService._is_safe_select_query("SELECT * FROM \"Product\";") is True
    assert AIService._is_safe_select_query("select price, name from Product join Category on categoryId=id;") is True
    
    # Invalid modification queries
    assert AIService._is_safe_select_query("DROP TABLE \"Product\";") is False
    assert AIService._is_safe_select_query("DELETE FROM \"Order\" WHERE id = '1';") is False
    assert AIService._is_safe_select_query("UPDATE \"Product\" SET price = 100;") is False
    assert AIService._is_safe_select_query("INSERT INTO \"Table\" (number) VALUES ('A5');") is False

if __name__ == "__main__":
    test_safe_select_query()
    print("AIService unit tests passed successfully!")
