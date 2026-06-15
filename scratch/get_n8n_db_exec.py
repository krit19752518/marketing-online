import asyncio
import asyncpg
import json

async def main():
    conn = await asyncpg.connect("postgresql://n8n_user:n8n_secure_password_99@localhost:5432/content_marketing")
    # Query execution_data
    row = await conn.fetchrow("SELECT * FROM execution_data WHERE \"executionId\" = '93'")
    if row:
        print(dict(row).keys())
        # The columns are likely executionId, data, etc. Let's print data
        data_text = row["data"]
        # If it is a string JSON, let's load it
        try:
            data = json.loads(data_text)
            if isinstance(data, list):
                print("Data is a list of length:", len(data))
                # Let's inspect each item
                for idx, item in enumerate(data):
                    print(f"Item {idx} keys:", item.keys() if hasattr(item, 'keys') else type(item))
                    if "error" in item:
                        print(f"  Error in item {idx}:", json.dumps(item["error"], indent=2))
                    if "runData" in item:
                        print(f"  RunData nodes:", item["runData"].keys())
                        for node, runs in item["runData"].items():
                            for r_idx, r in enumerate(runs):
                                if "error" in r:
                                    print(f"    Node {node} Run {r_idx} Error:", json.dumps(r["error"], indent=2))
            else:
                print("Data is a dict. Keys:", data.keys())
        except Exception as e:
            print("Failed to parse data column:", e)
            print("Raw data sample:", data_text[:200])
    await conn.close()

asyncio.run(main())
