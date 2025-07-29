import os
from typing import Dict

temp_files: Dict[str, str] = {}

def add_temp_file(file_id: str, file_path: str):
    temp_files[file_id] = file_path

def get_temp_file_path(file_id: str) -> str | None:
    return temp_files.get(file_id)

def remove_temp_file(file_id: str):
    file_path = temp_files.pop(file_id, None)
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            print(f"Error deleting temp file {file_path}: {str(e)}")

def cleanup_all_temp_files():
    for file_id in list(temp_files.keys()): # Iterate over a copy of keys
        remove_temp_file(file_id)