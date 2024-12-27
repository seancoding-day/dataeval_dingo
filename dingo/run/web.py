import os
import uvicorn
from io import BytesIO
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse
from zipfile import ZipFile, ZIP_DEFLATED

from dingo.model import Model
from dingo.exec import Executor, ExecProto
from dingo.io import InputArgs

app = FastAPI(title='dingo: Tool for detect language quality')

def create_zip_from_path(path: str, zip_buff: BytesIO):
    with ZipFile(zip_buff, 'w', compression=ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, path)
                zipf.write(file_path, arcname=arcname)

@app.get("/")
def readme():
    return {'Hello! Get more infomation, please read: https://github.com/shijinpjlab/Dingo'}

@app.get("/download/")
def download_file(path: str):
    print(path)

    if not os.path.exists(path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Path not found: "+path)

    zip_buff = BytesIO()

    create_zip_from_path(path, zip_buff)

    zip_buff.seek(0)
    headers = {
        "Content-Disposition": f"attachment; filename={os.path.basename(path)}.zip"
    }
    return StreamingResponse(zip_buff, media_type="application/zip", headers=headers)

@app.post("/main/")
def eval_local(raw: InputArgs):
    Model.apply_config(raw.custom_config)

    executor: ExecProto = Executor.exec_map['local'](raw)
    return executor.evaluate()

if __name__ == '__main__':
    uvicorn.run(app=app, host="127.0.0.1", port=8087)
