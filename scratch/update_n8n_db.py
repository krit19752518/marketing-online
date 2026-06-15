import psycopg2
import json
import os

# Read TikTok_Flow.json
flow_path = "/home/krit/my-office/TikTok_Flow.json"
with open(flow_path, "r", encoding="utf-8") as f:
    flow_data = json.load(f)

nodes = flow_data.get("nodes", [])
connections = flow_data.get("connections", {})

# Connect to n8n database
try:
    conn = psycopg2.connect(
        dbname="content_marketing",
        user="n8n_user",
        password="n8n_secure_password_99",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()
    
    # Update nodes and connections for ct8PdAzqcjrjHL4x
    cur.execute(
        """
        UPDATE workflow_entity 
        SET nodes = %s, connections = %s, "updatedAt" = NOW()
        WHERE id = %s;
        """,
        (json.dumps(nodes), json.dumps(connections), "ct8PdAzqcjrjHL4x")
    )
    conn.commit()
    print("Successfully updated workflow 'ct8PdAzqcjrjHL4x' (TikTok Flow) in PostgreSQL database!")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error updating n8n database: {e}")
