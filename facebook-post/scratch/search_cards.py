import sqlite3
import os

db_path = "/home/krit/my-office/facebook-post/facebook-post.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT itemid, title, status, slide1_bg_path, slide2_bg_path, slide3_bg_path FROM shopee_affiliate_cards")
rows = cur.fetchall()
for r in rows:
    print(dict(r))
conn.close()
