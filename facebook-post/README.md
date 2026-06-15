# Shopee Affiliate Caption Dashboard (Phase 1)

Quick start (Linux):

1. create a python venv and install:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. copy env and run:

```bash
cp .env.example .env
export DATABASE_PATH=facebook-post.db
./run.sh
```

3. Open http://localhost:5000 to view the simple dashboard.

Import CSV example:

```bash
python import_csv.py /path/to/file.csv facebook-post.db
```
