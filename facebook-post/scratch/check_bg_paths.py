import sqlite3
import os

db_path = "/home/krit/my-office/facebook-post/facebook-post.db"
print(f"DB Path: {db_path} exists={os.path.exists(db_path)}")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT itemid, status, slide1_bg_path, slide2_bg_path, slide3_bg_path, slide1_final_path, slide2_final_path, slide3_final_path FROM shopee_affiliate_cards WHERE itemid = ?", ("44900790127",))
row = cur.fetchone()
if row:
    print(dict(row))
else:
    print("Item not found")
conn.close()
