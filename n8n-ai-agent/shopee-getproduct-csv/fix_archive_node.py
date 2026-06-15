#!/usr/bin/env python3
"""
fix_all_nodes.py
Update all 3 Execute Command nodes in the Shopee-GetProduct-csv workflow
so their output is piped to /proc/1/fd/1 (container stdout → docker logs).
"""
import json
import psycopg2

CONN = {
    "host": "localhost",
    "port": 5432,
    "dbname": "content_marketing",
    "user": "n8n_user",
    "password": "n8n_secure_password_99",
}

# Updated commands for each node
NODE_UPDATES = {
    "Filter Shopee CSV": (
        "/home/node/.n8n/shopee-getproduct-csv/run_filter.sh | tee -a /proc/1/fd/1"
    ),
    "Bulk Copy to DB": (
        "CSV_PATH=/data/shopee-raw-data/today-download-data/shopee_filtered_$(date +%Y%m%d).csv "
        "node /home/node/.n8n/shopee-getproduct-csv/import_to_db.js | tee -a /proc/1/fd/1"
    ),
    "Archive Files": (
        'sh /home/node/.n8n/shopee-getproduct-csv/move_files.sh '
        '"$(ls -t /data/shopee-raw-data/today-download-data/*.csv | grep -v shopee_filtered | head -1)" '
        '"/data/shopee-raw-data/today-download-data/shopee_filtered_$(date +%Y%m%d).csv" '
        "| tee -a /proc/1/fd/1"
    ),
}

def main():
    conn = psycopg2.connect(**CONN)
    cur = conn.cursor()

    # Fetch current nodes JSON
    cur.execute(
        "SELECT id, nodes FROM workflow_entity WHERE name = 'Shopee-GetProduct-csv';"
    )
    row = cur.fetchone()
    if not row:
        print("ERROR: Workflow 'Shopee-GetProduct-csv' not found.")
        return

    wf_id, nodes_raw = row
    nodes = json.loads(nodes_raw) if isinstance(nodes_raw, str) else nodes_raw

    # Update each node
    for node in nodes:
        name = node.get("name")
        if name in NODE_UPDATES:
            old_cmd = node["parameters"].get("command", "")
            new_cmd = NODE_UPDATES[name]
            print(f"\n[{name}]")
            print(f"  before: {old_cmd}")
            print(f"  after:  {new_cmd}")
            node["parameters"]["command"] = new_cmd

    # Write back
    cur.execute(
        "UPDATE workflow_entity SET nodes = %s WHERE id = %s;",
        (json.dumps(nodes), wf_id),
    )
    conn.commit()
    print("\nSUCCESS: All 3 nodes updated.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
