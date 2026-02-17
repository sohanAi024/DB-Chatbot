from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dynamic DB globals
active_engine = None
ActiveSessionLocal = None

def get_db():
    """
    Dependency to get the primary database session.
    Always use the primary database for authentication and core app state.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_data_db():
    """
    Dependency to get the data database session.
    Use dynamic session if available, else fallback to primary for data queries.
    """
    if ActiveSessionLocal:
        db = ActiveSessionLocal()
    else:
        db = SessionLocal()
    
    try:
        yield db
    finally:
        db.close()

def connect_to_db(database_url: str):
    """
    Connects to a dynamic database for the session.
    """
    global active_engine, ActiveSessionLocal
    try:
        # Create new engine
        new_engine = create_engine(database_url)
        # Test connection
        with new_engine.connect() as connection:
            pass
            
        # Update globals if successful
        active_engine = new_engine
        ActiveSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=active_engine)
        return True, "Connected successfully"
    except Exception as e:
        return False, str(e)
