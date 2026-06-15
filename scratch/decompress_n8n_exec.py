import asyncio
import asyncpg
import json

async def main():
    conn = await asyncpg.connect("postgresql://n8n_user:n8n_secure_password_99@localhost:5432/content_marketing")
    # Fetch execution data for run ID 101
    row = await conn.fetchrow("SELECT * FROM execution_data WHERE \"executionId\" = '101'")
    if not row:
        print("No execution data found.")
        await conn.close()
        return
        
    data = json.loads(row["data"])
    
    # In n8n compressed JSON:
    # data[0] contains the structure metadata.
    # The subsequent elements are the de-duplicated objects/strings.
    # The main run data is at data[2]
    # Decompress main_obj to find the exact error details of execution 101
    main_obj = data[2]
    
    def get_val(val):
        if isinstance(val, str) and val.isdigit():
            idx = int(val)
            if idx < len(data):
                return data[idx]
        return val

    decompressed = {}
    for k, v in main_obj.items():
        k_val = get_val(k)
        v_val = get_val(v)
        decompressed[k_val] = v_val
        
    print("Decompressed main keys:", decompressed.keys())
    if "error" in decompressed:
        error_val = get_val(decompressed["error"])
        # Resolve error dict keys
        resolved_err = {}
        if isinstance(error_val, dict):
            for ek, ev in error_val.items():
                resolved_err[get_val(ek)] = get_val(ev)
        print("Main Error:", json.dumps(resolved_err, indent=2, ensure_ascii=False))
        
    # Extract runData
    run_data_idx = main_obj.get("runData")
    if run_data_idx:
        run_data = get_val(run_data_idx)
        if isinstance(run_data, dict):
            # Resolve all keys of run_data
            resolved_keys = [get_val(k) for k in run_data.keys()]
            print("RunData Node Names:", resolved_keys)
        else:
            print("runData is not a dict:", type(run_data))
            
    await conn.close()

asyncio.run(main())
