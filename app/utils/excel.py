import pandas as pd
import os, uuid, tempfile

def generate_excel(data):
    df = pd.DataFrame(data)
    file_id = str(uuid.uuid4())
    file_path = os.path.join(tempfile.gettempdir(), f"{file_id}.xlsx")
    df.to_excel(file_path, index=False)
    return file_id, file_path
