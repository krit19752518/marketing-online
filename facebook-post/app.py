import os
# Reloaded due to .env change
import json
import sqlite3
import tempfile
import queue
import threading
import logging
import requests
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
from ai_service import generate_shopee_caption, log_prompt_history
from tiktok_service import generate_tiktok_caption, compose_tiktok_slide_image

load_dotenv(override=True)
DB_PATH = os.getenv('DATABASE_PATH', 'facebook-post.db')
FB_PAGE_ID = os.getenv('FB_PAGE_ID')
FB_PAGE_ACCESS_TOKEN = os.getenv('FB_PAGE_ACCESS_TOKEN')

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logging.info("Initializing Shopee Affiliate Caption application...")
app = Flask(__name__, static_folder='static')

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = sqlite3.connect(DB_PATH)
    migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
    if os.path.exists(migrations_dir):
        sql_files = sorted([f for f in os.listdir(migrations_dir) if f.endswith('.sql')])
        for sql_file in sql_files:
            file_path = os.path.join(migrations_dir, sql_file)
            with open(file_path, 'r', encoding='utf-8') as f:
                sql = f.read()
                try:
                    conn.executescript(sql)
                except Exception as e:
                    print(f"Error applying migration {sql_file}: {e}")
    # Cleanup old error reviewer notes for successfully generated captions
    try:
        conn.execute("UPDATE shopee_affiliate_cards SET reviewer_note = NULL WHERE status = 'ai_generated' AND reviewer_note LIKE 'AI Generation Error%'")
    except Exception as e:
        print(f"Error during db cleanup: {e}")
    conn.commit()
    conn.close()

# ---------------------------------------------------------------------------
# Background Worker — Facebook Caption (Ollama)
# ---------------------------------------------------------------------------
task_queue = queue.Queue()

def background_worker():
    logging.info("Background worker thread started.")
    while True:
        itemid = task_queue.get()
        if itemid is None:
            break
        logging.info(f"[Queue Worker] Processing AI caption for item ID: {itemid}")
        try:
            db = get_db()
            cur = db.execute('SELECT * FROM shopee_affiliate_cards WHERE itemid = ?', (itemid,))
            card = cur.fetchone()
            if card:
                card_dict = dict(card)
                prompt, caption, error = generate_shopee_caption(card_dict)
                log_prompt_history(DB_PATH, itemid, prompt, caption or "", error)
                if error:
                    logging.error(f"[Queue Worker] Error generating caption for {itemid}: {error}")
                    db.execute('UPDATE shopee_affiliate_cards SET reviewer_note = ?, updated_at = datetime(\'now\') WHERE itemid = ?',
                               (f"AI Generation Error: {error}", itemid))
                else:
                    logging.info(f"[Queue Worker] Successfully generated caption for {itemid}")
                    db.execute('UPDATE shopee_affiliate_cards SET ai_caption = ?, ai_prompt = ?, status = ?, reviewer_note = NULL, updated_at = datetime(\'now\') WHERE itemid = ?',
                               (caption, prompt, 'ai_generated', itemid))
                db.commit()
        except Exception as e:
            logging.error(f"[Queue Worker] Exception in generation worker for {itemid}: {e}", exc_info=True)
        finally:
            task_queue.task_done()

# Start Facebook caption worker thread
worker_thread = threading.Thread(target=background_worker, daemon=True)
worker_thread.start()

# ---------------------------------------------------------------------------
# Background Worker — TikTok (Ollama-only Combined Script & Prompts)
# ---------------------------------------------------------------------------
tiktok_task_queue = queue.Queue()

def tiktok_background_worker():
    logging.info("TikTok background worker thread started.")
    while True:
        itemid = tiktok_task_queue.get()
        if itemid is None:
            break
        logging.info(f"[TikTok Worker] Processing item ID: {itemid}")
        try:
            db = get_db()
            cur = db.execute('SELECT * FROM shopee_affiliate_cards WHERE itemid = ?', (itemid,))
            card = cur.fetchone()
            if not card:
                logging.warning(f"[TikTok Worker] Item {itemid} not found in DB, skipping.")
                continue

            card_dict = dict(card)

            # Ollama: generate JSON containing scripts + prompts
            logging.info(f"[TikTok Worker] Calling Ollama for combined TikTok scripts/prompts for item {itemid}")
            result_json_str, error = generate_tiktok_caption(card_dict)

            if error or not result_json_str:
                logging.error(f"[TikTok Worker] Ollama failed for {itemid}: {error}")
                db.execute(
                    "UPDATE shopee_affiliate_cards SET status = 'tiktok-prompt-generated', "
                    "reviewer_note = ?, updated_at = datetime('now') WHERE itemid = ?",
                    (f"TikTok Error (Ollama): {error}", itemid)
                )
                db.commit()
                continue

            # Parse JSON to format database fields for dashboard compatibility
            try:
                data = json.loads(result_json_str)
                # Format prompts: Slide 1: ...\n\nSlide 2: ...\n\nSlide 3: ...
                formatted_prompt = (
                    f"Slide 1: {data.get('prompt_bg_1', '').strip()}\n\n"
                    f"Slide 2: {data.get('prompt_bg_2', '').strip()}\n\n"
                    f"Slide 3: {data.get('prompt_bg_3', '').strip()}"
                )
                # Format captions: Slide 1: ...\n\nSlide 2: ...\n\nSlide 3: ...
                formatted_caption = (
                    f"Slide 1: {data.get('slide_1_hook', '').strip()}\n\n"
                    f"Slide 2: {data.get('slide_2_value', '').strip()}\n\n"
                    f"Slide 3: {data.get('slide_3_cta', '').strip()}"
                )
                
                db.execute(
                    "UPDATE shopee_affiliate_cards "
                    "SET status = 'tiktok-prompt-generated', ai_caption = ?, ai_prompt = ?, "
                    "reviewer_note = NULL, updated_at = datetime('now') WHERE itemid = ?",
                    (formatted_caption, formatted_prompt, itemid)
                )
                db.commit()
                logging.info(f"[TikTok Worker] Successfully generated scripts and prompts for item {itemid}")
            except Exception as parse_exc:
                logging.error(f"[TikTok Worker] Failed to parse Ollama JSON response: {parse_exc}")
                db.execute(
                    "UPDATE shopee_affiliate_cards SET status = 'tiktok-prompt-generated', "
                    "ai_caption = ?, reviewer_note = ?, updated_at = datetime('now') WHERE itemid = ?",
                    (result_json_str, f"TikTok JSON parse warning: {parse_exc}", itemid)
                )
                db.commit()

        except Exception as exc:
            logging.error(f"[TikTok Worker] Exception for {itemid}: {exc}", exc_info=True)
            try:
                db.execute(
                    "UPDATE shopee_affiliate_cards SET reviewer_note = ?, updated_at = datetime('now') WHERE itemid = ?",
                    (f"TikTok System Error: {str(exc)}", itemid)
                )
                db.commit()
            except Exception:
                pass
        finally:
            tiktok_task_queue.task_done()

# Start TikTok worker thread
tiktok_worker_thread = threading.Thread(target=tiktok_background_worker, daemon=True)
tiktok_worker_thread.start()

@app.route('/cards', methods=['GET'])
def list_cards():
    status = request.args.get('status')
    campaign = request.args.get('campaign')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    q = 'SELECT * FROM shopee_affiliate_cards'
    conditions = []
    params = []
    if status:
        conditions.append('status = ?')
        params.append(status)
    if campaign:
        conditions.append('source_filename = ?')
        params.append(campaign)
    if conditions:
        q += ' WHERE ' + ' AND '.join(conditions)
    q += ' ORDER BY updated_at DESC, discount_percentage DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])
    db = get_db()
    cur = db.execute(q, params)
    rows = [dict(r) for r in cur.fetchall()]
    return jsonify(rows)


@app.route('/cards/<itemid>', methods=['GET'])
def get_card(itemid):
    db = get_db()
    cur = db.execute('SELECT * FROM shopee_affiliate_cards WHERE itemid = ?', (itemid,))
    row = cur.fetchone()
    if not row:
        return jsonify({'error': 'not found'}), 404
    return jsonify(dict(row))

@app.route('/cards/<itemid>', methods=['PATCH'])
def update_card(itemid):
    data = request.json or {}
    allowed = [
        'status', 'ai_caption', 'reviewer_note', 'assigned_to', 'ai_prompt',
        'slide1_bg_path', 'slide2_bg_path', 'slide3_bg_path',
        'slide1_final_path', 'slide2_final_path', 'slide3_final_path'
    ]
    fields = {k: data[k] for k in data.keys() if k in allowed}
    if not fields:
        return jsonify({'error': 'no updatable fields provided'}), 400
    
    if 'status' in fields:
        new_status = fields['status']
        valid_statuses = ['new', 'ai_generated', 'review', 'approved', 'posted', 'tiktok-posted', 'tiktok-prompt-generated', 'rejected']
        if new_status not in valid_statuses:
            return jsonify({'error': f'Invalid status: {new_status}'}), 400
            
        db = get_db()
        cur = db.execute('SELECT status, ai_caption FROM shopee_affiliate_cards WHERE itemid = ?', (itemid,))
        row = cur.fetchone()
        if not row:
            return jsonify({'error': 'not found'}), 404
        
        current_status = row['status']
        caption = row['ai_caption']
        if new_status in ['approved', 'posted'] and not caption and 'ai_caption' not in fields:
            return jsonify({'error': 'Cannot approve or post card without AI caption.'}), 400
            
    set_clause = ', '.join([f"{k} = ?" for k in fields.keys()]) + ', updated_at = datetime(\'now\')'
    params = list(fields.values()) + [itemid]
    db = get_db()
    db.execute(f'UPDATE shopee_affiliate_cards SET {set_clause} WHERE itemid = ?', params)
    db.commit()
    return get_card(itemid)

@app.route('/cards/<itemid>/upload-bg', methods=['POST'])
def upload_slide_background(itemid):
    slide = request.args.get('slide')
    if not slide or slide not in ['1', '2', '3']:
        return jsonify({'error': 'Invalid or missing slide parameter (must be 1, 2, or 3)'}), 400
        
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in request'}), 400
        
    f = request.files['file']
    if f.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
        
    # Create uploads directory if it doesn't exist
    uploads_dir = os.path.join(app.static_folder, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Save file securely
    ext = os.path.splitext(f.filename)[1].lower() or '.png'
    filename = f"bg_{itemid}_slide_{slide}{ext}"
    file_path = os.path.join(uploads_dir, filename)
    f.save(file_path)
    
    # Update DB with background path
    db_relative_path = f"/static/uploads/{filename}"
    bg_field = f"slide{slide}_bg_path"
    
    db = get_db()
    db.execute(
        f"UPDATE shopee_affiliate_cards SET {bg_field} = ?, updated_at = datetime('now') WHERE itemid = ?",
        (db_relative_path, itemid)
    )
    db.commit()
    
    logging.info(f"[API] Uploaded background slide {slide} for card {itemid} -> {db_relative_path}")
    return get_card(itemid)

@app.route('/cards/<itemid>/compose-tiktok', methods=['POST'])
def compose_tiktok_slides_endpoint(itemid):
    data = request.json or {}
    db = get_db()
    cur = db.execute('SELECT * FROM shopee_affiliate_cards WHERE itemid = ?', (itemid,))
    card = cur.fetchone()
    if not card:
        return jsonify({'error': 'Card not found'}), 404
        
    card_dict = dict(card)
    
    # Retrieve slide text content from request payload or DB
    slide1_text = data.get('slide1_text')
    slide2_text = data.get('slide2_text')
    slide3_text = data.get('slide3_text')
    
    # If not provided in request, parse from ai_caption in DB
    db_caption = card_dict.get('ai_caption') or ""
    if not slide1_text or not slide2_text or not slide3_text:
        # Fallback to splitting DB text if formatted in Slide 1:...
        if "Slide 1:" in db_caption and "Slide 2:" in db_caption:
            p1 = db_caption.split('Slide 2:')
            s1_val = p1[0].replace('Slide 1:', '').strip()
            p23 = (p1[1] if len(p1) > 1 else '').split('Slide 3:')
            s2_val = p23[0].strip()
            s3_val = (p23[1] if len(p23) > 1 else '').strip()
            
            slide1_text = slide1_text or s1_val
            slide2_text = slide2_text or s2_val
            slide3_text = slide3_text or s3_val
        else:
            # Entire text is slide 1 fallback
            slide1_text = slide1_text or db_caption
            slide2_text = slide2_text or ""
            slide3_text = slide3_text or ""

    # Prepare composition folders
    composed_dir = os.path.join(app.static_folder, 'composed')
    os.makedirs(composed_dir, exist_ok=True)
    
    # Slide backgrounds
    bg1 = os.path.join(app.root_path, card_dict.get('slide1_bg_path').lstrip('/')) if card_dict.get('slide1_bg_path') else None
    bg2 = os.path.join(app.root_path, card_dict.get('slide2_bg_path').lstrip('/')) if card_dict.get('slide2_bg_path') else None
    bg3 = os.path.join(app.root_path, card_dict.get('slide3_bg_path').lstrip('/')) if card_dict.get('slide3_bg_path') else None
    
    # Price info dict to pass for Slide 2 overlay rendering
    price_info = {
        'price': card_dict.get('price'),
        'sale_price': card_dict.get('sale_price'),
        'discount_percentage': card_dict.get('discount_percentage')
    }
    
    # Render slide images
    composed_path_1 = os.path.join(composed_dir, f"composed_{itemid}_slide_1.png")
    composed_path_2 = os.path.join(composed_dir, f"composed_{itemid}_slide_2.png")
    composed_path_3 = os.path.join(composed_dir, f"composed_{itemid}_slide_3.png")
    
    try:
        # Slide 1 composition
        compose_tiktok_slide_image(
            bg1, card_dict.get('image_link'), slide1_text, 
            composed_path_1, 1
        )
        # Slide 2 composition
        compose_tiktok_slide_image(
            bg2, card_dict.get('image_link'), slide2_text, 
            composed_path_2, 2, price_info=price_info
        )
        # Slide 3 composition
        compose_tiktok_slide_image(
            bg3, card_dict.get('image_link'), slide3_text, 
            composed_path_3, 3
        )
        
        # Save output paths to DB
        rel_path_1 = f"/static/composed/composed_{itemid}_slide_1.png"
        rel_path_2 = f"/static/composed/composed_{itemid}_slide_2.png"
        rel_path_3 = f"/static/composed/composed_{itemid}_slide_3.png"
        
        # Save updated texts as well
        formatted_caption = (
            f"Slide 1: {slide1_text.strip()}\n\n"
            f"Slide 2: {slide2_text.strip()}\n\n"
            f"Slide 3: {slide3_text.strip()}"
        )
        
        # Update DB
        db.execute(
            "UPDATE shopee_affiliate_cards SET "
            "ai_caption = ?, "
            "slide1_final_path = ?, slide2_final_path = ?, slide3_final_path = ?, "
            "status = 'review', updated_at = datetime('now') WHERE itemid = ?",
            (formatted_caption, rel_path_1, rel_path_2, rel_path_3, itemid)
        )
        db.commit()
        logging.info(f"[API] Programmatic composition complete for item {itemid}")
        return get_card(itemid)
    except Exception as compose_err:
        logging.error(f"[API] Composition failed for item {itemid}: {compose_err}", exc_info=True)
        return jsonify({'error': f"Composition failed: {str(compose_err)}"}), 500

@app.route('/cards/import', methods=['POST'])
def import_endpoint():
    if 'file' in request.files:
        f = request.files['file']
        if f.filename == '':
            return jsonify({'error': 'empty filename'}), 400
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        try:
            f.save(tmp.name)
            from import_csv import upsert_from_csv
            upsert_from_csv(tmp.name, DB_PATH)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            try:
                tmp.close()
                os.unlink(tmp.name)
            except Exception:
                pass
        return jsonify({'status': 'imported'})

    body = request.json or {}
    path = body.get('csv_path')
    if not path:
        return jsonify({'error': 'csv_path required'}), 400
    try:
        from import_csv import upsert_from_csv
        upsert_from_csv(path, DB_PATH)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'status': 'imported'})

@app.route('/cards/<itemid>/generate', methods=['POST'])
def generate_caption_endpoint(itemid):
    db = get_db()
    cur = db.execute('SELECT * FROM shopee_affiliate_cards WHERE itemid = ?', (itemid,))
    card = cur.fetchone()
    if not card:
        return jsonify({'error': 'Card not found'}), 404
    
    logging.info(f"Generating caption inline for item ID: {itemid}")
    prompt, caption, error = generate_shopee_caption(dict(card))
    log_prompt_history(DB_PATH, itemid, prompt, caption or "", error)
    if error:
        logging.error(f"Inline AI Generation error for {itemid}: {error}")
        db.execute('UPDATE shopee_affiliate_cards SET reviewer_note = ?, updated_at = datetime(\'now\') WHERE itemid = ?',
                   (f"AI Generation Error: {error}", itemid))
        db.commit()
        return jsonify({'error': error}), 500
    
    logging.info(f"Inline AI Generation successful for {itemid}")
    db.execute('UPDATE shopee_affiliate_cards SET ai_caption = ?, ai_prompt = ?, status = ?, reviewer_note = NULL, updated_at = datetime(\'now\') WHERE itemid = ?',
               (caption, prompt, 'ai_generated', itemid))
    db.commit()
    return get_card(itemid)

@app.route('/cards/batch-generate', methods=['POST'])
def batch_generate_endpoint():
    data = request.json or {}
    itemids = data.get('itemids')
    if not itemids or not isinstance(itemids, list):
        return jsonify({'error': 'itemids list required'}), 400
    logging.info(f"Queueing batch generation for {len(itemids)} items.")
    for itemid in itemids:
        task_queue.put(itemid)
    return jsonify({'status': 'queued', 'count': len(itemids)})

@app.route('/cards/<itemid>/prompt-history', methods=['GET'])
def get_prompt_history(itemid):
    db = get_db()
    cur = db.execute('SELECT * FROM ai_prompt_history WHERE itemid = ? ORDER BY created_at DESC', (itemid,))
    rows = [dict(r) for r in cur.fetchall()]
    return jsonify(rows)

@app.route('/cards/batch-post-fb', methods=['POST'])
def batch_post_fb_endpoint():
    data = request.json or {}
    itemids = data.get('itemids')
    if not itemids or not isinstance(itemids, list):
        return jsonify({'error': 'itemids list required'}), 400
    
    if not FB_PAGE_ID or not FB_PAGE_ACCESS_TOKEN:
        return jsonify({'error': 'Facebook Page credentials not configured in .env'}), 500

    logging.info(f"Received batch-post-fb request for item IDs: {itemids}")
    results = {'success': 0, 'failed': 0, 'details': []}
    db = get_db()
    
    for itemid in itemids:
        cur = db.execute('SELECT * FROM shopee_affiliate_cards WHERE itemid = ?', (itemid,))
        card = cur.fetchone()
        if not card:
            results['failed'] += 1
            results['details'].append({'itemid': itemid, 'error': 'Not found'})
            continue
            
        card_dict = dict(card)
        if card_dict.get('status') not in ['approved', 'ai_generated']:
            results['failed'] += 1
            results['details'].append({'itemid': itemid, 'error': f"Card is in status '{card_dict.get('status')}', must be 'approved' or 'ai_generated'"})
            continue
            
        caption = card_dict.get('ai_caption')
        image_url = card_dict.get('image_link')
        link = card_dict.get('product_short_link') or card_dict.get('product_link') or ""
        
        if not caption:
            results['failed'] += 1
            results['details'].append({'itemid': itemid, 'error': 'No AI caption found'})
            continue

        # Post to Facebook Graph API as a Link Share (Feed Post)
        # This makes the generated link preview card clickable directly to Shopee
        fb_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
        payload = {
            'message': caption,
            'link': link,
            'access_token': FB_PAGE_ACCESS_TOKEN
        }

        try:
            logging.info(f"Posting item {itemid} to Facebook Page feed as a Link Share...")
            response = requests.post(fb_url, data=payload)
            resp_data = response.json()
            
            if response.status_code == 200 and ('id' in resp_data or 'post_id' in resp_data):
                # Success
                db.execute("UPDATE shopee_affiliate_cards SET status = 'posted', reviewer_note = NULL, updated_at = datetime('now') WHERE itemid = ?", (itemid,))
                db.commit()
                results['success'] += 1
                results['details'].append({'itemid': itemid, 'status': 'success', 'fb_response': resp_data})
            else:
                # FB API Error
                error_msg = resp_data.get('error', {}).get('message', 'Unknown FB API error')
                db.execute("UPDATE shopee_affiliate_cards SET reviewer_note = ?, updated_at = datetime('now') WHERE itemid = ?", (f"FB Post Error: {error_msg}", itemid))
                db.commit()
                results['failed'] += 1
                results['details'].append({'itemid': itemid, 'error': error_msg})
        except Exception as e:
            logging.error(f"Error posting item {itemid} to FB: {e}")
            db.execute("UPDATE shopee_affiliate_cards SET reviewer_note = ?, updated_at = datetime('now') WHERE itemid = ?", (f"System Error: {str(e)}", itemid))
            db.commit()
            results['failed'] += 1
            results['details'].append({'itemid': itemid, 'error': str(e)})

    return jsonify(results)

@app.route('/cards/batch-post-tiktok', methods=['POST'])
def batch_post_tiktok_endpoint():
    """Queue selected cards for TikTok prompt generation (Ollama → Gemini).
    Runs fully in Flask — no n8n dependency."""
    data = request.json or {}
    itemids = data.get('itemids')
    if not itemids or not isinstance(itemids, list):
        return jsonify({'error': 'itemids list required'}), 400

    logging.info(f"[TikTok] Received batch request for item IDs: {itemids}")
    results = {'success': 0, 'failed': 0, 'details': []}
    db = get_db()

    for itemid in itemids:
        cur = db.execute('SELECT itemid, title FROM shopee_affiliate_cards WHERE itemid = ?', (itemid,))
        card = cur.fetchone()
        if not card:
            results['failed'] += 1
            results['details'].append({'itemid': itemid, 'error': 'Card not found'})
            continue

        # Mark as queued immediately so UI shows progress
        db.execute(
            "UPDATE shopee_affiliate_cards "
            "SET reviewer_note = 'กำลังสร้าง TikTok prompt...', updated_at = datetime('now') "
            "WHERE itemid = ?",
            (itemid,)
        )
        db.commit()

        tiktok_task_queue.put(itemid)
        logging.info(f"[TikTok] Queued item {itemid} — '{dict(card).get('title', '')[:40]}'")
        results['success'] += 1
        results['details'].append({'itemid': itemid, 'status': 'queued'})

    return jsonify(results)

@app.route('/logs', methods=['GET'])
def get_system_logs():
    log_file = 'app.log'
    if not os.path.exists(log_file):
        return jsonify([])
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return jsonify(lines[-100:])
    except Exception as e:
        return jsonify([f"Error reading logs: {e}"])

@app.route('/webhook', methods=['GET'])
def webhook_verify():
    verify_token = os.getenv('FB_VERIFY_TOKEN', 'RateDeeDeeVerifyToken123')
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if mode and token:
        if mode == 'subscribe' and token == verify_token:
            logging.info("[Webhook] Verification successful.")
            return challenge, 200
        else:
            logging.warning("[Webhook] Verification failed: token mismatch.")
            return 'Forbidden', 403
    return 'Bad Request', 400

@app.route('/webhook', methods=['POST'])
def webhook_event():
    data = request.json or {}
    if data.get('object') == 'page':
        for entry in data.get('entry', []):
            for messaging_event in entry.get('messaging', []):
                sender_id = messaging_event.get('sender', {}).get('id')
                if not sender_id:
                    continue
                if 'message' in messaging_event:
                    msg = messaging_event['message']
                    if 'text' in msg and not msg.get('is_echo'):
                        text = msg['text']
                        from chatbot_service import handle_chatbot_message
                        handle_chatbot_message(sender_id, text)
                elif 'postback' in messaging_event:
                    payload = messaging_event['postback'].get('payload')
                    if payload:
                        from chatbot_service import handle_chatbot_postback
                        handle_chatbot_postback(sender_id, payload)
        return 'EVENT_RECEIVED', 200
    else:
        return 'Not Found', 404

@app.route('/catalog.csv', methods=['GET'])
def get_catalog_feed():
    import io
    import csv
    from flask import Response
    
    db = get_db()
    # Retrieve only approved items to display on our page storefront
    cur = db.execute("SELECT * FROM shopee_affiliate_cards WHERE status = 'approved'")
    rows = cur.fetchall()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write Facebook Catalog Headers
    writer.writerow([
        'id', 'title', 'description', 'availability', 'condition', 
        'price', 'sale_price', 'link', 'image_link', 'brand', 
        'custom_label_0', 'custom_label_1'
    ])
    
    for row in rows:
        d = dict(row)
        
        # Calculate custom system signal labels (custom_label_0)
        labels = []
        discount = d.get('discount_percentage') or 0
        sold = d.get('item_sold') or 0
        
        if discount >= 50:
            labels.append("Hot Deal")
        if sold >= 500:
            labels.append("Best Seller")
        if d.get('is_official_shop') == 1:
            labels.append("Official Store")
        
        custom_label_0 = ", ".join(labels) if labels else "Normal"
        custom_label_1 = d.get('category') or "หมวดหมู่อื่นๆ"
        
        # Format prices to match Facebook Commerce requirements (Value + Currency)
        original_price = f"{d.get('price') or 0.0:.2f} THB"
        sale_price = f"{d.get('sale_price') or 0.0:.2f} THB"
        
        brand = "Shopee"
        if d.get('is_official_shop') == 1:
            brand = "Official Store"
        elif d.get('is_preferred_shop') == 1:
            brand = "Preferred Store"
            
        desc = d.get('ai_caption') or d.get('description') or d.get('title')
        
        writer.writerow([
            d.get('itemid'),
            d.get('title'),
            desc,
            'in stock' if (d.get('stock') or 1) > 0 else 'out of stock',
            'new',
            original_price,
            sale_price,
            d.get('product_short_link') or d.get('product_link'),
            d.get('image_link'),
            brand,
            custom_label_0,
            custom_label_1
        ])
        
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers["Content-Disposition"] = "attachment; filename=catalog.csv"
    return response

@app.route('/proxy-image', methods=['GET'])
def proxy_image():
    url = request.args.get('url')
    if not url:
        return 'Missing url parameter', 400
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        }
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        content_type = res.headers.get('Content-Type', 'image/jpeg')
        from flask import Response
        response = Response(res.content, mimetype=content_type)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        logging.error(f"Error in proxy-image: {str(e)}")
        return f"Error fetching image: {str(e)}", 500

@app.route('/')
def dashboard():
    return send_from_directory(app.static_folder, 'dashboard.html')

if __name__ == '__main__':
    logging.info("Starting database migration check...")
    init_db()
    logging.info("Starting Flask application on port 5000...")
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=False)
    # Trigger reload for env updates

