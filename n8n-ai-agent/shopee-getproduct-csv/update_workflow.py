import json
import psycopg2

# Database connection string
db_url = "postgresql://n8n_user:n8n_secure_password_99@localhost:5432/content_marketing"

# ---------------------------------------------------------------------------
# Nodes definition – Manual trigger → Filter → Discord → Import → Archive
# ---------------------------------------------------------------------------
nodes = [
    {
        "parameters": {},
        "id": "node_manual",
        "name": "Execute",
        "type": "n8n-nodes-base.manualTrigger",
        "typeVersion": 1,
        "position": [100, 200]
    },
    {
        "parameters": {
            "command": "/home/node/.n8n/shopee-getproduct-csv/run_filter.sh",
            "captureOutput": True
        },

        "id": "node_filter",
        "name": "Filter Shopee CSV",
        "type": "n8n-nodes-base.executeCommand",
        "typeVersion": 1,
        "position": [300, 200]
    },

    {
        "parameters": {
            "command": "CSV_PATH=/data/shopee-raw-data/today-download-data/shopee_filtered_$(date +%Y%m%d).csv node /home/node/.n8n/shopee-getproduct-csv/import_to_db.js",
            "options": {"captureOutput": True}
        },
        "id": "node_import",
        "name": "Bulk Copy to DB",
        "type": "n8n-nodes-base.executeCommand",
        "typeVersion": 1,
        "position": [550, 200]
    },
    {
        "parameters": {
            "command": "sh /home/node/.n8n/shopee-getproduct-csv/move_files.sh $(ls -t /data/shopee-raw-data/today-download-data/*.csv | grep -v shopee_filtered | head -1) /data/shopee-raw-data/today-download-data/shopee_filtered_$(date +%Y%m%d).csv",
            "options": {"captureOutput": True}
        },
        "id": "node_archive",
        "name": "Archive Files",
        "type": "n8n-nodes-base.executeCommand",
        "typeVersion": 1,
        "position": [800, 200]
    }
]

# ---------------------------------------------------------------------------
# Connections – linear flow
# ---------------------------------------------------------------------------
connections = {
    "Execute": {
        "main": [[{"node": "Filter Shopee CSV", "type": "main", "index": 0}]]
    },
    "Filter Shopee CSV": {
        "main": [[{"node": "Bulk Copy to DB", "type": "main", "index": 0}]]
    },
    "Bulk Copy to DB": {
        "main": [[{"node": "Archive Files", "type": "main", "index": 0}]]
    }
}

settings = {"executionOrder": "v1"}

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute(
        "UPDATE workflow_entity SET nodes = %s, connections = %s, settings = %s WHERE id = 'QoByMxliB4ZmD2Hc';",
        (json.dumps(nodes), json.dumps(connections), json.dumps(settings))
    )
    conn.commit()
    print("Workflow updated successfully in DB.")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
