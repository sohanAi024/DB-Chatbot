import uvicorn
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app.models.base import Base
# Import all models to ensure they are registered with Base.metadata
from app.models import user, conversation 
from app.routers import auth, conversations, data, chat
from app.utils.temp_files import cleanup_all_temp_files

# Load environment variables from .env file
load_dotenv()

# Ensure tables are created on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="User Management API with LangGraph Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(conversations.router)
app.include_router(data.router)
app.include_router(chat.router)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.on_event("shutdown")
def shutdown_event():
    cleanup_all_temp_files()

if __name__ == "__main__":
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))
    uvicorn.run(app, host=host, port=port)
