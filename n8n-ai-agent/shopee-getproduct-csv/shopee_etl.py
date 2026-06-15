#!/usr/bin/env python3
"""
Shopee ETL Pipeline (Standalone)
- Download/Read Shopee CSV
- Filter products by criteria
- Clean encoding issues
- Import to PostgreSQL
- Logging + Error handling
"""

import os
import sys
import csv
import psycopg2
import logging
from datetime import datetime
from pathlib import Path
import io # <<< เพิ่มบรรทัดนี้

# ============================================================================
# CONFIGURATION
# ============================================================================

# Database
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'content_marketing')
DB_USER = os.getenv('DB_USER', 'n8n_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'n8n_secure_password_99')

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.getenv('SHOPEE_DATA_DIR', os.path.join(BASE_DIR, 'product-data', 'today-download-data'))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
TEMP_DIR = os.path.join(BASE_DIR, 'temp')

# Create directories if they don't exist
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
Path(TEMP_DIR).mkdir(parents=True, exist_ok=True)
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

# Logging setup
# Logging setup (Modified for real-time and historical logs)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # Set default level

# Formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Timestamped file handler
timestamped_log_file = os.path.join(LOG_DIR, f"shopee_etl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
file_handler = logging.FileHandler(timestamped_log_file)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Latest log file handler (overwrites on each run)
latest_log_file = os.path.join(LOG_DIR, 'shopee_etl_latest.log')
latest_file_handler = logging.FileHandler(latest_log_file, mode='w') # 'w' to overwrite each time
latest_file_handler.setFormatter(formatter)
logger.addHandler(latest_file_handler)

# Console handler
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def sanitize_text(text):
    """Remove null bytes and invalid UTF-8 characters"""
    if text is None:
        return ''
    if isinstance(text, str):
        # Remove null bytes
        text = text.replace('\x00', '')
        # Remove control characters except tab, newline
        text = ''.join(c for c in text if ord(c) >= 32 or c in '\t\n\r')
        return text
    return str(text)

# Global buffer size for reading chunks
CHUNK_SIZE = 1024 * 1024 * 5 # 5 MB (Adjust as needed for performance vs memory)

def clean_csv_file(input_file):
    """
    Read CSV file as binary, remove null bytes, and create a cleaned,
    temporarily decoded file. Processes in chunks to handle large files.
    """
    logger.info(f"Cleaning CSV file: {input_file}")
    temp_cleaned_binary_file = os.path.join(TEMP_DIR, 'shopee_cleaned.bin')
    temp_final_csv_file = os.path.join(TEMP_DIR, 'shopee_cleaned.csv')

    original_size = 0
    cleaned_size = 0
    null_bytes_removed = 0

    try:
        # Step 1: Remove null bytes from binary data and write to an intermediate binary file
        logger.info("Step 1/2: Removing null bytes (\\x00) from binary file...")
        with open(input_file, 'rb') as infile_binary, \
             open(temp_cleaned_binary_file, 'wb') as outfile_binary:
            while True:
                chunk = infile_binary.read(CHUNK_SIZE)
                if not chunk:
                    break
                original_size += len(chunk)
                
                cleaned_chunk = chunk.replace(b'\x00', b'')
                outfile_binary.write(cleaned_chunk)
                cleaned_size += len(cleaned_chunk)
                null_bytes_removed += (len(chunk) - len(cleaned_chunk))

        logger.info(f"Original file size: {original_size:,} bytes")
        logger.info(f"Cleaned binary file size: {cleaned_size:,} bytes (removed {null_bytes_removed:,} null bytes)")
        
        # Step 2: Decode the cleaned binary file to UTF-8 and write to the final CSV file
        logger.info("Step 2/2: Decoding cleaned binary file to UTF-8...")
        encoding_tried = 'utf-8'
        try:
            with open(temp_cleaned_binary_file, 'rb') as infile_cleaned_binary, \
                 open(temp_final_csv_file, 'w', encoding='utf-8', errors='replace') as outfile_text:
                for line_bytes in infile_cleaned_binary:
                    # Attempt UTF-8 decoding for each line
                    line_text = line_bytes.decode('utf-8', errors='replace')
                    outfile_text.write(line_text)

        except Exception as e:
            # Fallback for more aggressive decoding if initial UTF-8 pass fails badly
            logger.warning(f"UTF-8 decode pass failed for {temp_cleaned_binary_file}: {e}, attempting full latin-1 pass as fallback...")
            encoding_tried = 'latin-1'
            with open(temp_cleaned_binary_file, 'rb') as infile_cleaned_binary, \
                 open(temp_final_csv_file, 'w', encoding='utf-8', errors='replace') as outfile_text: # Output still UTF-8
                for line_bytes in infile_cleaned_binary:
                    line_text = line_bytes.decode('latin-1', errors='replace')
                    outfile_text.write(line_text)
            
        logger.info(f"Cleaned and decoded CSV saved to: {temp_final_csv_file} (initial decoding via {encoding_tried})")
        
        # Clean up intermediate binary file
        os.remove(temp_cleaned_binary_file)
        logger.debug(f"Removed temporary binary file: {temp_cleaned_binary_file}")

        return temp_final_csv_file
        
    except Exception as e:
        logger.error(f"Error cleaning CSV: {e}", exc_info=True)
        # Attempt to clean up any temporary files if an error occurs
        if os.path.exists(temp_cleaned_binary_file):
            os.remove(temp_cleaned_binary_file)
        if os.path.exists(temp_final_csv_file):
            os.remove(temp_final_csv_file)
        raise

def filter_products(input_csv):
    """
    Filter products by criteria:
    - Discount > 30%
    - Lowest Price Guarantee = Yes
    - (Official or Preferred shop) + Discount > 0%
    """
    logger.info(f"Filtering products from: {input_csv}")
    
    output_csv = os.path.join(DATA_DIR, f"shopee_filtered_{datetime.now().strftime('%Y%m%d')}.csv")
    
    db_columns = [
        'itemid', 'shopid', 'title', 'price', 'sale_price', 'discount_percentage',
        'stock', 'item_sold', 'item_rating', 'likes_count', 'is_preferred_shop',
        'is_official_shop', 'has_lowest_price_guarantee', 'image_link',
        'product_link', 'product_short_link', 'global_category1', 'global_category2',
        'global_category3', 'shop_name', 'seller_name', 'global_brand',
        'description', 'model_names', 'model_prices'
    ]
    
    def should_include(row):
        """Filter logic"""
        is_official = (row.get('is_official_shop') == 'Official shop' or row.get('is_official_shop') in ('1', 'True', 'true'))
        is_preferred = (row.get('is_preferred_shop') == 'Preferred shop' or row.get('is_preferred_shop') in ('1', 'True', 'true'))
        
        if not (is_official or is_preferred):
            return False
            
        try:
            sold = int(float(row.get('item_sold', 0)))
        except ValueError:
            sold = 0
            
        try:
            rating = float(row.get('item_rating', 0))
        except ValueError:
            rating = 0.0
            
        return sold > 50 or rating > 4.0
    
    def map_row(row):
        """Map CSV to DB columns"""
        return {
            'itemid': sanitize_text(row.get('itemid', '')),
            'shopid': sanitize_text(row.get('shopid', '')),
            'title': sanitize_text(row.get('title', '')),
            'price': sanitize_text(row.get('price', '')),
            'sale_price': sanitize_text(row.get('sale_price', '')),
            'discount_percentage': sanitize_text(row.get('discount_percentage', '')),
            'stock': sanitize_text(row.get('stock', '')),
            'item_sold': sanitize_text(row.get('item_sold', '')),
            'item_rating': sanitize_text(row.get('item_rating', '')),
            'likes_count': sanitize_text(row.get('like', '')),
            'is_preferred_shop': sanitize_text(row.get('is_preferred_shop', '')),
            'is_official_shop': sanitize_text(row.get('is_official_shop', '')),
            'has_lowest_price_guarantee': sanitize_text(row.get('has_lowest_price_guarantee', '')),
            'image_link': sanitize_text(row.get('image_link', '')),
            'product_link': sanitize_text(row.get('product_link', '')),
            'product_short_link': sanitize_text(row.get('product_short link', '')),
            'global_category1': sanitize_text(row.get('global_category1', '')),
            'global_category2': sanitize_text(row.get('global_category2', '')),
            'global_category3': sanitize_text(row.get('global_category3', '')),
            'shop_name': sanitize_text(row.get('shop_name', '')),
            'seller_name': sanitize_text(row.get('seller_name', '')),
            'global_brand': sanitize_text(row.get('global_brand', '')),
            'description': sanitize_text(row.get('description', '')),
            'model_names': sanitize_text(row.get('model_names', '')),
            'model_prices': sanitize_text(row.get('model_prices', '')),
        }
    
    try:
        matched_count = 0
        total_count = 0
        
        with open(input_csv, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            
            with open(output_csv, 'w', encoding='utf-8', newline='') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=db_columns)
                writer.writeheader()
                
                for row in reader:
                    total_count += 1
                    if should_include(row):
                        mapped = map_row(row)
                        writer.writerow(mapped)
                        matched_count += 1
                    
                    if total_count % 100000 == 0:
                        logger.info(f"Processed {total_count:,} rows, matched {matched_count:,}")
        
        logger.info(f"Filtering complete. Total: {total_count:,}, Matched: {matched_count:,}")
        logger.info(f"Filtered CSV saved to: {output_csv}")
        return output_csv
        
    except Exception as e:
        logger.error(f"Error filtering products: {e}")
        raise

def import_to_database(csv_file):
    """
    Import filtered CSV to PostgreSQL using staging table for price history time-series
    """
    logger.info(f"Importing CSV to database: {csv_file}")
    
    conn = None
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        cursor = conn.cursor()
        logger.info(f"Connected to {DB_NAME} @ {DB_HOST}:{DB_PORT}")
        
        # 1. Create temporary staging table
        logger.info("Creating temporary staging table...")
        cursor.execute("CREATE TEMP TABLE temp_shopee_import (LIKE shopee_discount_products INCLUDING DEFAULTS);")
        
        # 2. Bulk copy into staging table
        logger.info("Starting bulk COPY into staging table...")
        with open(csv_file, 'r', encoding='utf-8') as f:
            cursor.copy_expert(
                """COPY temp_shopee_import (
                    itemid, shopid, title, price, sale_price, discount_percentage,
                    stock, item_sold, item_rating, likes_count, is_preferred_shop,
                    is_official_shop, has_lowest_price_guarantee, image_link,
                    product_link, product_short_link, global_category1, global_category2,
                    global_category3, shop_name, seller_name, global_brand,
                    description, model_names, model_prices
                ) FROM STDIN WITH CSV HEADER""",
                f
            )
            
        # 3. Upsert products dimension
        logger.info("Upserting records into shopee_products table...")
        cursor.execute("""
            INSERT INTO shopee_products (
                itemid, shopid, title, image_link, product_link, product_short_link,
                global_category1, global_category2, global_category3, shop_name,
                seller_name, global_brand, description, model_names
            )
            SELECT DISTINCT 
                itemid, shopid, title, image_link, product_link, product_short_link,
                global_category1, global_category2, global_category3, shop_name,
                seller_name, global_brand, description, model_names
            FROM temp_shopee_import
            ON CONFLICT (itemid) DO UPDATE SET
                title = EXCLUDED.title,
                image_link = EXCLUDED.image_link,
                product_link = EXCLUDED.product_link,
                product_short_link = EXCLUDED.product_short_link,
                global_category1 = EXCLUDED.global_category1,
                global_category2 = EXCLUDED.global_category2,
                global_category3 = EXCLUDED.global_category3,
                shop_name = EXCLUDED.shop_name,
                seller_name = EXCLUDED.seller_name,
                global_brand = EXCLUDED.global_brand,
                description = EXCLUDED.description,
                model_names = EXCLUDED.model_names,
                updated_at = CURRENT_TIMESTAMP;
        """)
        
        # 4. Insert price history fact
        logger.info("Inserting price history records into shopee_price_history table...")
        cursor.execute("""
            INSERT INTO shopee_price_history (
                itemid, price, sale_price, discount_percentage, stock, item_sold,
                item_rating, likes_count, is_preferred_shop, is_official_shop,
                has_lowest_price_guarantee, recorded_date
            )
            SELECT 
                itemid, price, sale_price, discount_percentage, stock, item_sold,
                item_rating, likes_count, is_preferred_shop, is_official_shop,
                has_lowest_price_guarantee, CURRENT_DATE
            FROM temp_shopee_import
            ON CONFLICT (itemid, recorded_date) DO UPDATE SET
                price = EXCLUDED.price,
                sale_price = EXCLUDED.sale_price,
                discount_percentage = EXCLUDED.discount_percentage,
                stock = EXCLUDED.stock,
                item_sold = EXCLUDED.item_sold,
                item_rating = EXCLUDED.item_rating,
                likes_count = EXCLUDED.likes_count,
                is_preferred_shop = EXCLUDED.is_preferred_shop,
                is_official_shop = EXCLUDED.is_official_shop,
                has_lowest_price_guarantee = EXCLUDED.has_lowest_price_guarantee;
        """)
        
        # 5. Populate shopee_discount_products for backward compatibility
        logger.info("Updating backward-compatible shopee_discount_products table...")
        cursor.execute('TRUNCATE TABLE shopee_discount_products;')
        cursor.execute('INSERT INTO shopee_discount_products SELECT * FROM temp_shopee_import;')
        
        conn.commit()
        
        # Get row count
        cursor.execute('SELECT COUNT(*) FROM shopee_discount_products;')
        row_count = cursor.fetchone()[0]
        logger.info(f"Import complete! Total rows in DB: {row_count:,}")
        
        cursor.close()
        
    except Exception as e:
        logger.error(f"Error importing to database: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def archive_files(csv_file):
    """Move processed files to archive directories"""
    logger.info(f"Archiving files...")
    
    try:
        old_data_dir = os.path.join(DATA_DIR, 'old-data')
        use_data_dir = os.path.join(DATA_DIR, 'use-data')
        
        Path(old_data_dir).mkdir(parents=True, exist_ok=True)
        Path(use_data_dir).mkdir(parents=True, exist_ok=True)
        
        # Move filtered CSV to use-data
        filename = os.path.basename(csv_file)
        dest = os.path.join(use_data_dir, filename)
        
        if os.path.exists(csv_file):
            os.rename(csv_file, dest)
            logger.info(f"Moved to use-data: {filename}")
        
    except Exception as e:
        logger.warning(f"Error archiving files: {e}")

# ============================================================================
# MAIN ETL PIPELINE
# ============================================================================

def main():
    """Execute ETL pipeline"""
    logger.info("=" * 80)
    logger.info("SHOPEE ETL PIPELINE START")
    logger.info("=" * 80)
    
    try:
        # Step 1: Find input CSV
        csv_files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith('.csv') and 'filtered' not in f])
        
        if not csv_files:
            logger.error("No input CSV found in data directory")
            return 1
        
        input_csv = os.path.join(DATA_DIR, csv_files[0])
        logger.info(f"Found input CSV: {csv_files[0]}")
        
        # Step 2: Clean CSV
        cleaned_csv = clean_csv_file(input_csv)
        
        # Step 3: Filter products
        filtered_csv = filter_products(cleaned_csv)
        
        # Step 4: Import to database
        import_to_database(filtered_csv)
        
        # Step 5: Archive
        archive_files(filtered_csv)
        
        logger.info("=" * 80)
        logger.info("SHOPEE ETL PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        logger.info("=" * 80)
        logger.info("SHOPEE ETL PIPELINE FAILED")
        logger.info("=" * 80)
        return 1

if __name__ == '__main__':
    sys.exit(main())
