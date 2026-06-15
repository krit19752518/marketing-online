import asyncio
import asyncpg
import json

async def main():
    conn = await asyncpg.connect("postgresql://n8n_user:n8n_secure_password_99@localhost:5432/content_marketing")
    row = await conn.fetchrow("SELECT * FROM execution_data WHERE \"executionId\" = '100'")
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

    # data[2] contains the runData
    run_data_raw = data[2].get("runData")
    if run_data_raw:
        run_data = resolve(run_data_raw)
        
        # Print Guardrail Classifier Output
        classifier_run = run_data.get("Guardrail Classifier")
        if classifier_run:
            print("=== Guardrail Classifier Node Output ===")
            print(json.dumps(classifier_run, indent=2, ensure_ascii=False))
            
        # Print Parse Classifier JSON Output
        parse_run = run_data.get("Parse Classifier JSON")
        if parse_run:
            print("=== Parse Classifier JSON Node Output ===")
            print(json.dumps(parse_run, indent=2, ensure_ascii=False))
            
    await conn.close()

asyncio.run(main())
