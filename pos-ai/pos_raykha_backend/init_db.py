from database import engine, Base, SessionLocal
from models import Tenant, CentralUser
import bcrypt

def init_db():
    print("Creating tables in pos_central...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if Demo Tenant exists
        demo_tenant = db.query(Tenant).filter(Tenant.db_name == "pos_ai_db").first()
        if not demo_tenant:
            print("Seeding Demo Tenant...")
            demo_tenant = Tenant(
                name="Demo Restaurant",
                db_name="pos_ai_db"
            )
            db.add(demo_tenant)
            db.commit()
            db.refresh(demo_tenant)
        
        # Check if Demo User exists
        demo_user = db.query(CentralUser).filter(CentralUser.username == "manager").first()
        if not demo_user:
            print("Seeding manager user...")
            hashed_pw = bcrypt.hashpw("password123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            demo_user = CentralUser(
                tenant_id=demo_tenant.id,
                username="manager",
                password=hashed_pw,
                name="Krit Owner",
                role="OWNER"
            )
            db.add(demo_user)
            db.commit()
            
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
