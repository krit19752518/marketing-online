import json
import subprocess

with open('/home/krit/my-office/workflow_md_modified.json', 'r') as f:
    data = json.load(f)

# Serialize nodes and connections
nodes_str = json.dumps(data['nodes'])
connections_str = json.dumps(data['connections'])

# Escape single quotes for SQL
nodes_str_escaped = nodes_str.replace("'", "''")
connections_str_escaped = connections_str.replace("'", "''")

sql_query = f"""
UPDATE workflow_entity 
SET nodes = '{nodes_str_escaped}'::jsonb, 
    connections = '{connections_str_escaped}'::jsonb 
WHERE id = 'ngHGoKsaRVwCIB5F';
"""

# Write to temp sql file
sql_file = '/home/krit/my-office/scratch/update_workflow.sql'
with open(sql_file, 'w') as f:
    f.write(sql_query)

# Execute via docker exec psql
cmd = [
    "docker", "exec", "-i", "content_marketing_db", 
    "psql", "-U", "n8n_user", "-d", "content_marketing"
]
process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
stdout, stderr = process.communicate(input=sql_query)

print("STDOUT:", stdout)
print("STDERR:", stderr)
