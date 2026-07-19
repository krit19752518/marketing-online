import os
import sys
import paramiko
from dotenv import load_dotenv

def deploy():
    load_dotenv()
    hostname = "143.14.36.234"
    username = "root"
    password = "Kr1t@12342518"
    token = os.getenv("GIT_TOKEN", "")

    print(f"Connecting to VPS {hostname}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(hostname, username=username, password=password, timeout=20)
        print("Connected successfully! Starting full system deployment...\n")

        # Define all commands to execute step-by-step
        commands = [
            # 1. Update or clone codebase on VPS
            f"if [ -d '/home/krit/my-office/marketing-online' ]; then "
            f"  cd /home/krit/my-office/marketing-online && git fetch --all && git reset --hard origin/main && git pull; "
            f"else "
            f"  git clone https://{token}@github.com/krit19752518/marketing-online.git /home/krit/my-office/marketing-online; "
            f"fi",
            
            # 2. Re-create symbolic link for pos-ai project folder
            "rm -f /home/krit/my-office/pos-ai && ln -s /home/krit/my-office/marketing-online/pos-ai /home/krit/my-office/pos-ai",
            
            # 3. Configure remote PostgreSQL roles & databases (port 5432)
            "su - postgres -c \"psql -c \\\"CREATE USER n8n_user WITH PASSWORD 'n8n_secure_pass_2026' SUPERUSER;\\\" || true\"",
            "su - postgres -c \"psql -c \\\"CREATE DATABASE pos_central OWNER n8n_user;\\\" || true\"",
            "su - postgres -c \"psql -c \\\"CREATE DATABASE pos_ai_db OWNER n8n_user;\\\" || true\"",

            # 4. Generate Node.js POS-AI backend .env on the VPS
            "cat << 'EOF' > /home/krit/my-office/pos-ai/backend/.env\n"
            "PORT=3000\n"
            'DATABASE_URL="postgresql://n8n_user:n8n_secure_pass_2026@localhost:5432/pos_ai_db?schema=public"\n'
            'DIRECT_URL="postgresql://n8n_user:n8n_secure_pass_2026@localhost:5432/pos_ai_db?schema=public"\n'
            'JWT_SECRET="pos_ai_jwt_secret_2026_change_on_production"\n'
            "EOF",

            # 5. Generate Python POS-Raykha backend .env on the VPS
            "cat << 'EOF' > /home/krit/my-office/pos-ai/pos_raykha_backend/.env\n"
            "HERMES_AI_API_KEY=sk-oM8Mc06hqozmhO4JQTz2jjqlc37YoY8nF4Ut6wGFGTXerurB\n"
            "HERMES_AI_BASE_URL=https://api.opentyphoon.ai/v1\n"
            "HERMES_AI_MODEL=typhoon-v2.5-30b-a3b-instruct\n"
            "CENTRAL_DATABASE_URL=postgresql+psycopg://n8n_user:n8n_secure_pass_2026@localhost:5432/pos_central\n"
            "DB_HOST=localhost\n"
            "DB_PORT=5432\n"
            "DB_USER=n8n_user\n"
            "DB_PASSWORD=n8n_secure_pass_2026\n"
            "HOST=0.0.0.0\n"
            "PORT=8002\n"
            "JWT_SECRET=pos_ai_jwt_secret_2026_change_on_production\n"
            "EOF",

            # 6. Deploy POS-AI Backend (NodeJS / Express / Prisma)
            "cd /home/krit/my-office/pos-ai/backend && npm install",
            "cd /home/krit/my-office/pos-ai/backend && npx prisma db push",
            "cd /home/krit/my-office/pos-ai/backend && npm run build",
            "pm2 delete pos-ai-backend || true",
            "cd /home/krit/my-office/pos-ai/backend && pm2 start dist/server.js --name 'pos-ai-backend'",

            # 7. Deploy POS-Raykha Backend (FastAPI / SQLAlchemy / Typhoon)
            "cd /home/krit/my-office/pos-ai/pos_raykha_backend && python3 -m venv venv",
            "cd /home/krit/my-office/pos-ai/pos_raykha_backend && PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 ./venv/bin/pip install --upgrade pip",
            "cd /home/krit/my-office/pos-ai/pos_raykha_backend && PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 ./venv/bin/pip install -r requirements.txt",
            "cd /home/krit/my-office/pos-ai/pos_raykha_backend && ./venv/bin/python init_db.py",
            "pm2 delete pos-raykha-backend || true",
            "cd /home/krit/my-office/pos-ai/pos_raykha_backend && pm2 start './venv/bin/uvicorn main:app --host 0.0.0.0 --port 8002' --name 'pos-raykha-backend'",

            # 8. Restore the old Raykha project backend on port 8001
            "pm2 delete raykha-backend || true",
            "cd /root/.hermes/raykha && pm2 start './venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001' --name 'raykha-backend'",

            # 9. Save PM2 state to auto-resume on server restarts
            "pm2 save",
            
            # 10. Output status
            "pm2 list"
        ]

        for cmd in commands:
            print(f"Running: {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            
            out_str = stdout.read().decode('utf-8')
            err_str = stderr.read().decode('utf-8')
            
            if out_str:
                print(f"[STDOUT]\n{out_str}")
            if err_str:
                print(f"[STDERR]\n{err_str}")
                
            print(f"Finished with exit status: {exit_status}\n" + "-"*50)

        print("\nFull System Deployment on VPS completed successfully!")

    except Exception as e:
        print(f"Deployment failed: {e}")
        sys.exit(1)
    finally:
        ssh.close()

if __name__ == "__main__":
    deploy()
