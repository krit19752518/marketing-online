import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    HERMES_AI_API_KEY = os.getenv("HERMES_AI_API_KEY", "")
    HERMES_AI_BASE_URL = os.getenv("HERMES_AI_BASE_URL", "https://api.opentyphoon.ai/v1")
    HERMES_AI_MODEL = os.getenv("HERMES_AI_MODEL", "typhoon-v2.5-30b-a3b-instruct")

    CENTRAL_DATABASE_URL = os.getenv("CENTRAL_DATABASE_URL", "postgresql+psycopg://n8n_user:n8n_secure_pass_2026@localhost:5435/pos_central")
    
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5435")
    DB_USER = os.getenv("DB_USER", "n8n_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "n8n_secure_pass_2026")

    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8001"))
    
    JWT_SECRET = os.getenv("JWT_SECRET", "pos_ai_jwt_secret_2026_change_on_production")
    JWT_ALGORITHM = "HS256"
