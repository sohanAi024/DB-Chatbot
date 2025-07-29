from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas import UserCreate
from app.models import User
from app.database import get_db
from app.utils.temp_files import temp_files, get_temp_file_path # Import temp_files and helper
from fastapi.responses import FileResponse
from datetime import datetime
import os

router = APIRouter()

@router.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return {"users": [user.to_dict() for user in users]}

@router.get("/download/{download_id}")
async def download_file(download_id: str):
    file_path = get_temp_file_path(download_id)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found or expired")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"user_data_export_{timestamp}.xlsx"
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )