import sys
import os

# Append current dir to path to import models and auth
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Usuario
from auth import get_password_hash

db = SessionLocal()

admin = db.query(Usuario).filter(Usuario.email == "admin@admin.com").first()
if not admin:
    admin = Usuario(
        nome="Administrador",
        email="admin@admin.com",
        telefone="11999999999",
        hashed_password=get_password_hash("admin123"),
        privilegio="admin"
    )
    db.add(admin)
    db.commit()
    print("Admin user created: admin@admin.com / admin123")
else:
    print("Admin user already exists.")

db.close()
