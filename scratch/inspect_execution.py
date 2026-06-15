import psycopg2
import json

conn = psycopg2.connect(
    dbname="content_marketing",
    user="n8n_user",
    password="n8n_secure_password_99",
    host="localhost",
    port="5432"
)
cur = conn.cursor()
cur.execute('SELECT data FROM execution_data WHERE "executionId" = %s;', ('392',))
row = cur.fetchone()
cur.close()
if row:
    data = row[0]
    if isinstance(data, str):
        data = json.loads(data)
    
    def safe_resolve(ref, visited=None):
        if visited is None:
            visited = set()
            
        if isinstance(ref, str) and ref.isdigit():
            ref = int(ref)
            
        if isinstance(ref, int):
            if ref in visited:
                return f"<Circular reference to index {ref}>"
            if ref >= len(data):
                return f"<Index {ref} out of bounds>"
            visited.add(ref)
            resolved = safe_resolve(data[ref], visited)
            visited.remove(ref)
            return resolved
        elif isinstance(ref, list):
            return [safe_resolve(x, visited) for x in ref]
        elif isinstance(ref, dict):
            return {k: safe_resolve(v, visited) for k, v in ref.items()}
        return ref

    # Let's find runData first
    run_data = None
    for item in data:
        if isinstance(item, dict) and 'runData' in item:
            run_data_ref = item['runData']
            run_data = safe_resolve(run_data_ref)
            break
            
    if run_data and 'Ollama Chain' in run_data:
        ollama_run = run_data['Ollama Chain']
        print("Ollama node run data:")
        if isinstance(ollama_run, list):
            ollama_run = ollama_run[0]
        print(json.dumps(ollama_run, indent=2, ensure_ascii=False)[:3000])
else:
    print("No execution data found for 392")
conn.close()
