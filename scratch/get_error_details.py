import asyncio
import asyncpg
import json

async def main():
    conn = await asyncpg.connect("postgresql://n8n_user:n8n_secure_password_99@localhost:5432/content_marketing")
    row = await conn.fetchrow("SELECT * FROM execution_data WHERE \"executionId\" = '93'")
    if row:
        data = json.loads(row["data"])
        # print execution objects that contain "error"
        for idx, item in enumerate(data):
            if isinstance(item, dict):
                # Search for error key recursively
                def find_errors(d, path=""):
                    if not isinstance(d, dict):
                        return
                    for k, v in d.items():
                        current_path = f"{path}.{k}" if path else k
                        if k.lower() == "error" and v:
                            print(f"[{idx}] Found error at {current_path}:", v)
                        elif isinstance(v, dict):
                            find_errors(v, current_path)
                        elif isinstance(v, list):
                            for i, val in enumerate(v):
                                find_errors(val, f"{current_path}[{i}]")
                find_errors(item)
    await conn.close()

asyncio.run(main())
