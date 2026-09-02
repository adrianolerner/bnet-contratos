import os
import subprocess
import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas, auth

router = APIRouter()

BACKUPS_DIR = "/app/backups"
os.makedirs(BACKUPS_DIR, exist_ok=True)

def get_db_url():
    # Extracts credentials from DATABASE_URL env var
    # e.g., postgresql://postgres:password@db:5432/bnet_contratos
    return os.getenv("DATABASE_URL")

@router.get("/backups")
def list_backups(current_user: models.Usuario = Depends(auth.get_current_active_admin)):
    files = []
    for f in os.listdir(BACKUPS_DIR):
        if f.endswith('.sql'):
            path = os.path.join(BACKUPS_DIR, f)
            stats = os.stat(path)
            files.append({
                "filename": f,
                "size": stats.st_size,
                "created_at": datetime.datetime.fromtimestamp(stats.st_ctime).isoformat()
            })
    files.sort(key=lambda x: x['created_at'], reverse=True)
    return files

@router.post("/backups")
def create_backup(current_user: models.Usuario = Depends(auth.get_current_active_admin)):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.sql"
    filepath = os.path.join(BACKUPS_DIR, filename)
    db_url = get_db_url()
    
    if not db_url:
        raise HTTPException(status_code=500, detail="DATABASE_URL is not set")
        
    try:
        command = [
            "pg_dump", 
            db_url, 
            "--clean", 
            "--if-exists", 
            "-f", filepath
        ]
        subprocess.run(command, check=True)
        return {"ok": True, "message": "Backup gerado com sucesso", "filename": filename}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar backup: {str(e)}")

@router.post("/backups/{filename}/restore")
def restore_backup(filename: str, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_active_admin)):
    filepath = os.path.join(BACKUPS_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Arquivo de backup não encontrado")
        
    db_url = get_db_url()
    if not db_url:
        raise HTTPException(status_code=500, detail="DATABASE_URL is not set")
        
    # Commit any pending transactions and close the session to release table locks
    db.commit()
    db.close()
    
    try:
        command = [
            "psql",
            db_url,
            "-f", filepath
        ]
        subprocess.run(command, check=True)
        return {"ok": True, "message": "Backup restaurado com sucesso"}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Erro ao restaurar backup: {str(e)}")

@router.delete("/backups/{filename}")
def delete_backup(filename: str, current_user: models.Usuario = Depends(auth.get_current_active_admin)):
    filepath = os.path.join(BACKUPS_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    os.remove(filepath)
    return {"ok": True}

@router.get("/backups/{filename}/download")
def download_backup(filename: str, current_user: models.Usuario = Depends(auth.get_current_active_admin)):
    filepath = os.path.join(BACKUPS_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(filepath, media_type="application/sql", filename=filename)

@router.post("/backups/upload")
def upload_backup(file: UploadFile = File(...), current_user: models.Usuario = Depends(auth.get_current_active_admin)):
    if not file.filename.endswith(".sql"):
        raise HTTPException(status_code=400, detail="Apenas arquivos .sql são permitidos")
        
    filepath = os.path.join(BACKUPS_DIR, file.filename)
    with open(filepath, "wb") as f:
        f.write(file.file.read())
    return {"ok": True, "message": "Backup enviado com sucesso"}
