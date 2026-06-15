import psycopg2
import json

try:
    conn = psycopg2.connect("postgresql://n8n_user:n8n_secure_password_99@localhost:5432/content_marketing")
    cur = conn.cursor()
    cur.execute("SELECT id, name, active, nodes::text, connections::text FROM workflow_entity ORDER BY name;")
    rows = cur.fetchall()
    
    for row in rows:
        w_id, name, active, nodes_str, conn_str = row
        nodes = json.loads(nodes_str)
        print(f"Workflow: {name} (ID: {w_id}), Active: {active}")
        trigger_nodes = [n for n in nodes if n.get('type', '').endswith('Trigger')]
        print(f"  Total nodes: {len(nodes)}")
        print(f"  Trigger nodes: {[n.get('name') + ' (' + n.get('type') + ')' for n in trigger_nodes]}")
        # Print trigger node parameters
        for tn in trigger_nodes:
            print(f"    Trigger node {tn.get('name')}: disabled={tn.get('disabled', False)}")
            
except Exception as e:
    print("Error:", e)
