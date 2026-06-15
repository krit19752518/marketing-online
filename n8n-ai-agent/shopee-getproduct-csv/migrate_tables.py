#!/usr/bin/env python3
import os
import psycopg2

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'content_marketing')
DB_USER = os.getenv('DB_USER', 'n8n_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'n8n_secure_password_99')

def main():
    print(f"Connecting to database {DB_NAME} at {DB_HOST}:{DB_PORT}...")
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cur = conn.cursor()
    
    try:
        print("Creating table shopee_products...")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS shopee_products (
            itemid BIGINT PRIMARY KEY,
            shopid BIGINT,
            title TEXT,
            image_link TEXT,
            product_link TEXT,
            product_short_link TEXT,
            global_category1 TEXT,
            global_category2 TEXT,
            global_category3 TEXT,
            shop_name TEXT,
            seller_name TEXT,
            global_brand TEXT,
            description TEXT,
            model_names TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        print("Creating table shopee_price_history...")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS shopee_price_history (
            id SERIAL PRIMARY KEY,
            itemid BIGINT REFERENCES shopee_products(itemid) ON DELETE CASCADE,
            price NUMERIC,
            sale_price NUMERIC,
            discount_percentage INT,
            stock INT,
            item_sold INT,
            item_rating NUMERIC,
            likes_count INT,
            is_preferred_shop VARCHAR(50),
            is_official_shop VARCHAR(50),
            has_lowest_price_guarantee VARCHAR(10),
            recorded_date DATE DEFAULT CURRENT_DATE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT uniq_item_date UNIQUE (itemid, recorded_date)
        );
        """)
        
        print("Creating indexes on shopee_price_history...")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_price_history_item_date ON shopee_price_history (itemid, recorded_date);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_price_history_recorded_date ON shopee_price_history (recorded_date);")
        
        conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    main()
