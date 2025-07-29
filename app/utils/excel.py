import pandas as pd
import os, uuid, tempfile

temp_files = {}

def generate_excel(data):
    df = pd.DataFrame(data)
    file_id = str(uuid.uuid4())
    file_path = os.path.join(tempfile.gettempdir(), f"{file_id}.xlsx")
    df.to_excel(file_path, index=False)
    temp_files[file_id] = file_path
    return file_id
