from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.agents.routers import users, chat
from app.database import engine, SessionLocal
from app.models import Base, User
from app.utils.temp_files import cleanup_all_temp_files # Import cleanup function
from datetime import datetime

app = FastAPI(title="User Management API with LangGraph Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api") # You might want to add a prefix
app.include_router(users.router, prefix="/api")

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Seed initial data if the users table is empty
        if db.query(User).count() == 0:
            db.add_all([
                User(name="John Doe", email="john@example.com", phone="555-0123", address="New York", salary=50000),
                User(name="Jane Smith", email="jane@example.com", phone="555-0124", address="California", salary=60000),
                User(name="Mehul Shah", email="mehul@example.com", phone="555-0125", address="Gujarat", salary=55000),
            ])
            db.commit()
    except Exception as e:
        print(f"Error during startup DB seeding: {e}")
    finally:
        db.close()

@app.on_event("shutdown")
def shutdown_event():
    cleanup_all_temp_files()