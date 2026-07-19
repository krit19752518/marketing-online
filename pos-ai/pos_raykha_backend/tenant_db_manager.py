from typing import Dict
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from config import Config
from models import Tenant
from tenant_models import TenantBase

class TenantDBManager:
    def __init__(self):
        # Cache for tenant database engines to prevent recreating connection pools
        self._engines: Dict[str, Engine] = {}
        # Cache for sessionmakers
        self._sessionmakers: Dict[str, sessionmaker] = {}

    def get_tenant_engine(self, tenant_id: str, central_db: Session) -> Engine:
        if tenant_id in self._engines:
            return self._engines[tenant_id]

        # Fetch tenant metadata from central database
        tenant = central_db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise ValueError(f"Tenant with ID {tenant_id} not found in central registry.")

        # Build PostgreSQL connection URL dynamically for this tenant database
        tenant_db_url = (
            f"postgresql+psycopg://{Config.DB_USER}:{Config.DB_PASSWORD}"
            f"@{Config.DB_HOST}:{Config.DB_PORT}/{tenant.db_name}"
        )
        
        print(f"Initializing connection pool for tenant: {tenant.name} ({tenant.db_name})")
        engine = create_engine(
            tenant_db_url,
            pool_size=5,
            max_overflow=10,
            pool_recycle=1800
        )

        # Auto-create Raykha chat history tables in this tenant's database if they don't exist
        print(f"Auto-creating/migrating Raykha tables in database '{tenant.db_name}'...")
        TenantBase.metadata.create_all(bind=engine)

        # Cache the engine
        self._engines[tenant_id] = engine
        self._sessionmakers[tenant_id] = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        return engine

    def get_tenant_session(self, tenant_id: str, central_db: Session) -> Session:
        self.get_tenant_engine(tenant_id, central_db)
        return self._sessionmakers[tenant_id]()

# Singleton instance of Tenant DB Manager
tenant_db_manager = TenantDBManager()
