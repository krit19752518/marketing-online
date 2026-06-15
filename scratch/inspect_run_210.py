import asyncio
import asyncpg
import json

async def main():
    conn = await asyncpg.connect("postgresql://n8n_user:n8n_secure_password_99@localhost:5432/content_marketing")
    row = await conn.fetchrow("SELECT * FROM execution_data WHERE \"executionId\" = 210")
    if not row:
        print("No execution data found.")
        await conn.close()
        return
        
    data = json.loads(row["data"])
    
    def resolve(val):
        if isinstance(val, str) and val.isdigit():
            idx = int(val)
            if idx < len(data):
                val = data[idx]
        if isinstance(val, dict):
            new_dict = {}
            for k, v in val.items():
                new_dict[resolve(k)] = resolve(v)
            return new_dict
        if isinstance(val, list):
            return [resolve(x) for x in val]
        return val

    run_data_raw = data[2].get("runData") if len(data) > 2 else None
    if run_data_raw:
        run_data = resolve(run_data_raw)
        print("Nodes that executed in run 210:")
        for node_name in run_data.keys():
            print(f"- Node: {node_name}")
            node_runs = run_data[node_name]
            if node_runs:
                for r in node_runs:
                    if "error" in r:
                        print("  Node Run Error:", json.dumps(r["error"], ensure_ascii=False))
                    if "data" in r and "main" not in r["data"] and "error" in r["data"]:
                        print("  Execution Error:", json.dumps(r["data"]["error"], ensure_ascii=False))
    await conn.close()

asyncio.run(main())
