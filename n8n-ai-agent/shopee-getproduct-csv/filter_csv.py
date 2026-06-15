#!/usr/bin/env python3
import sys
import os
import argparse
import csv

def sanitize_text(text):
    """Remove null bytes and invalid UTF-8 characters"""
    if text is None:
        return ''
    if isinstance(text, str):
        # Remove null bytes
        text = text.replace('\x00', '')
        # Remove other control characters except tab, newline
        text = ''.join(c for c in text if ord(c) >= 32 or c in '\t\n\r')
        return text
    return str(text)

def detect_file_encoding(file_path):
    """Try to detect file encoding by attempting to read with multiple encodings"""
    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read(1000)  # Try reading first 1000 chars
            print(f"File encoding detected: {encoding}", flush=True)
            return encoding
        except (UnicodeDecodeError, LookupError):
            continue
    
    print("Could not detect encoding, using utf-8 with error handling", flush=True)
    return 'utf-8'

parser = argparse.ArgumentParser(description='Filter Shopee CSV')
parser.add_argument('--input', help='Path to input CSV file', default=os.getenv('INPUT_CSV'))
parser.add_argument('--output', help='Path to output filtered CSV file', default=os.getenv('OUTPUT_CSV'))
args = parser.parse_args()

input_file = args.input if args.input else "/data/shared-media/shopee/shopee_products.csv"
output_file = args.output if args.output else "/data/shared-media/shopee/shopee_filtered.csv"

# If running outside Docker for testing, use local paths when defaults point to missing path
if not os.path.exists("/data/shared-media/shopee"):
    input_file = args.input if args.input else "/home/krit/my-office/content-marketing-infra/shared-media/shopee/shopee_products.csv"
    output_file = args.output if args.output else "/home/krit/my-office/content-marketing-infra/shared-media/shopee/shopee_filtered.csv"

# DB Columns in exact order
db_columns = [
    'itemid', 'shopid', 'title', 'price', 'sale_price', 'discount_percentage',
    'stock', 'item_sold', 'item_rating', 'likes_count', 'is_preferred_shop',
    'is_official_shop', 'has_lowest_price_guarantee', 'image_link',
    'product_link', 'product_short_link', 'global_category1', 'global_category2',
    'global_category3', 'shop_name', 'seller_name', 'global_brand',
    'description', 'model_names', 'model_prices'
]

def filter_row(row):
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
    # Map CSV fields to DB columns
    # Sanitize all values to remove null bytes and invalid UTF-8
    mapped = {}
    mapped['itemid'] = sanitize_text(row.get('itemid', ''))
    mapped['shopid'] = sanitize_text(row.get('shopid', ''))
    mapped['title'] = sanitize_text(row.get('title', ''))
    mapped['price'] = sanitize_text(row.get('price', ''))
    mapped['sale_price'] = sanitize_text(row.get('sale_price', ''))
    mapped['discount_percentage'] = sanitize_text(row.get('discount_percentage', ''))
    mapped['stock'] = sanitize_text(row.get('stock', ''))
    mapped['item_sold'] = sanitize_text(row.get('item_sold', ''))
    mapped['item_rating'] = sanitize_text(row.get('item_rating', ''))
    mapped['likes_count'] = sanitize_text(row.get('like', ''))  # 'like' in CSV -> 'likes_count' in DB
    mapped['is_preferred_shop'] = sanitize_text(row.get('is_preferred_shop', ''))
    mapped['is_official_shop'] = sanitize_text(row.get('is_official_shop', ''))
    mapped['has_lowest_price_guarantee'] = sanitize_text(row.get('has_lowest_price_guarantee', ''))
    mapped['image_link'] = sanitize_text(row.get('image_link', ''))
    mapped['product_link'] = sanitize_text(row.get('product_link', ''))
    mapped['product_short_link'] = sanitize_text(row.get('product_short link', ''))  # 'product_short link' in CSV -> 'product_short_link' in DB
    mapped['global_category1'] = sanitize_text(row.get('global_category1', ''))
    mapped['global_category2'] = sanitize_text(row.get('global_category2', ''))
    mapped['global_category3'] = sanitize_text(row.get('global_category3', ''))
    mapped['shop_name'] = sanitize_text(row.get('shop_name', ''))
    mapped['seller_name'] = sanitize_text(row.get('seller_name', ''))
    mapped['global_brand'] = sanitize_text(row.get('global_brand', ''))
    mapped['description'] = sanitize_text(row.get('description', ''))
    mapped['model_names'] = sanitize_text(row.get('model_names', ''))
    mapped['model_prices'] = sanitize_text(row.get('model_prices', ''))
    return mapped

print(f"Starting streaming filter process. Input: {input_file}, Output: {output_file}")

# First, clean the input CSV file by reading it as binary and removing null bytes
print("Pre-processing input file to remove null bytes and invalid UTF-8 sequences in streaming mode...")
temp_cleaned_file = input_file + ".cleaned"

try:
    import codecs
    chunk_size = 1024 * 1024 # 1MB
    decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
    
    with open(input_file, 'rb') as infile:
        with open(temp_cleaned_file, 'w', encoding='utf-8') as outfile:
            while True:
                chunk = infile.read(chunk_size)
                if not chunk:
                    break
                # Remove all null bytes from binary chunk
                chunk = chunk.replace(b'\x00', b'')
                # Decode incrementally
                text_chunk = decoder.decode(chunk)
                outfile.write(text_chunk)
            
            # Flush final bytes
            text_chunk = decoder.decode(b'', final=True)
            if text_chunk:
                outfile.write(text_chunk)
                
    print(f"Pre-processing complete. Cleaned file saved to: {temp_cleaned_file}", flush=True)
    input_file_to_use = temp_cleaned_file
    
except Exception as preprocess_err:
    print(f"Pre-processing failed: {preprocess_err}, continuing with original file...", flush=True)
    input_file_to_use = input_file

try:
    with open(input_file_to_use, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        
        with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=db_columns)
            writer.writeheader()
            
            matched_count = 0
            total_count = 0
            for row in reader:
                total_count += 1
                if filter_row(row):
                    mapped = map_row(row)
                    writer.writerow(mapped)
                    matched_count += 1
                    
                if total_count % 100000 == 0:
                    status_msg = f"Processed {total_count} / 1,000,000 rows ({total_count/10000:.1f}%), found {matched_count} matches..."
                    print(status_msg, flush=True)
                    try:
                        # Write progress to a text file inside the output directory (today-download-data)
                        progress_dir = os.path.dirname(output_file)
                        progress_file = os.path.join(progress_dir, "progress.txt")
                        with open(progress_file, "w", encoding="utf-8") as pf:
                            pf.write(status_msg)
                    except Exception as pe:
                        print(f"Error writing progress: {pe}", flush=True)
                        
    final_status = f"Filtering complete. Total rows: {total_count}, Saved: {matched_count}"
    print(final_status, flush=True)
    try:
        progress_dir = os.path.dirname(output_file)
        progress_file = os.path.join(progress_dir, "progress.txt")
        with open(progress_file, "w", encoding="utf-8") as pf:
            pf.write(final_status)
    except Exception as pe:
        print(f"Error writing final progress: {pe}", flush=True)
    
    # Clean up temp file if it was created
    if input_file_to_use != input_file and os.path.exists(temp_cleaned_file):
        try:
            os.remove(temp_cleaned_file)
            print(f"Cleaned temp file removed: {temp_cleaned_file}", flush=True)
        except:
            pass
            
except Exception as e:
    print(f"Error during execution: {e}")
    sys.exit(1)
