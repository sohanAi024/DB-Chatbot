import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from app.database import get_db, get_data_db, connect_to_db
from app.utils.auth import get_current_user
from app.utils.temp_files import get_temp_file_path

router = APIRouter(prefix="/api", tags=["data"])

class DBConnectionRequest(BaseModel):
    database_url: str

@router.post("/connect-db")
async def connect_db_endpoint(request: DBConnectionRequest):
    success, message = connect_to_db(request.database_url)
    if success:
        return {"status": "success", "message": message}
    else:
        raise HTTPException(status_code=400, detail=message)

@router.get("/schema")
def get_schema(db: Session = Depends(get_data_db), current_user = Depends(get_current_user)):
    try:
        tables = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
        schema = []
        for table in tables:
            table_name = table[0]
            columns = db.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'")).fetchall()
            col_details = [{"name": col[0], "type": col[1]} for col in columns]
            schema.append({"table_name": table_name, "columns": col_details})
        return {"schema": schema}
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/{table_name}")
def get_table_data(table_name: str, db: Session = Depends(get_data_db)):
    try:
        # Safe quoting for table name in postgres
        query = text(f'SELECT * FROM "{table_name}" LIMIT 100')
        result = db.execute(query)
        columns = result.keys()
        
        data = []
        for row in result.fetchall():
            row_dict = {}
            for col, val in zip(columns, row):
                row_dict[col] = val
            data.append(row_dict)
            
        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{download_id}")
async def download_file(download_id: str):
    file_path = get_temp_file_path(download_id)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found or expired")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data_export_{timestamp}.xlsx"
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
