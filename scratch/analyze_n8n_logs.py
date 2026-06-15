with open("/home/krit/my-office/scratch/n8n_all_logs.txt", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "error" in line.lower() or "fail" in line.lower() or "warn" in line.lower() or "discord" in line.lower() or "community" in line.lower():
        if "has no node to start the workflow" in line:
            # Skip repeating errors to keep output clean
            continue
        print(f"Line {i}: {line.strip()}")
