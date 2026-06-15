import sqlite3
import time
from ai_service import generate_shopee_caption

def test_campaign_generation():
    conn = sqlite3.connect('facebook-post.db')
    conn.row_factory = sqlite3.Row
    
    campaigns = ['GRADE AAA', 'VOLUME SHOCK', 'MICRO-TRIGGER']
    
    for camp in campaigns:
        print(f"\n==================================================")
        print(f"TESTING CAMPAIGN: {camp}")
        print(f"==================================================")
        
        # Select 2 new items for this campaign
        rows = conn.execute(
            "SELECT * FROM shopee_affiliate_cards WHERE source_filename = ? AND status = 'new' LIMIT 2",
            (camp,)
        ).fetchall()
        
        if not rows:
            print("No new items found.")
            continue
            
        for i, row in enumerate(rows):
            print(f"\n--- Item {i+1}: {row['title'][:50]}... (Discount: {row['discount_percentage']}%) ---")
            t0 = time.time()
            prompt, caption, error = generate_shopee_caption(dict(row))
            duration = time.time() - t0
            
            print(f"Time Taken: {duration:.2f} seconds")
            if error:
                print(f"Error: {error}")
            else:
                print("Generated Caption:")
                print(caption)
            print("-" * 40)

if __name__ == "__main__":
    test_campaign_generation()
