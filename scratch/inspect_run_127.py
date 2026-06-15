import asyncio
import asyncpg
import json

async def main():
    conn = await asyncpg.connect("postgresql://n8n_user:n8n_secure_password_99@localhost:5432/content_marketing")
    row = await conn.fetchrow("SELECT * FROM execution_data WHERE \"executionId\" = 127")
    if not row:
        print("Execution 127 data not found.")
        await conn.close()
        return
        
    data = json.loads(row["data"])
    
    # Let's see the keys in data
    # In n8n execution data, data[2] is runData, but since it's a list, the elements are indexed.
    # To resolve the references:
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
        print("Nodes that executed in run 127:")
        for node_name in run_data.keys():
            print(f"- Node: {node_name}")
            node_runs = run_data[node_name]
            if node_runs:
                # print output json
                out_json = node_runs[0].get("data", {}).get("main", [[{}]])[0][0].get("json", {})
                print("  Output:", json.dumps(out_json, ensure_ascii=False)[:300])
    else:
        print("No runData found in execution 127.")
    await conn.close()

asyncio.run(main())
