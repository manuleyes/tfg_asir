"""
Script para crear usuario admin de prueba
Ejecutar una sola vez
"""
import sys
sys.path.insert(0, '.')

from models.database import SessionLocal, engine, Base
from models.user import User
from auth.password_hash import hash_password

# Crear tablas
Base.metadata.create_all(bind=engine)

# Crear sesión
db = SessionLocal()

# Verificar si admin existe
existing = db.query(User).filter(User.username == "admin").first()
if existing:
    print(" Usuario admin ya existe")
    db.close()
    sys.exit(0)

# Crear usuario admin
admin = User(
    username="admin",
    password_hash=hash_password("admin123"),
    email="admin@vigilancia.local",
    is_active=True,
    is_admin=True
)

db.add(admin)
db.commit()
db.refresh(admin)

print(f" Usuario admin creado exitosamente!")
print(f"   Usuario: admin")
print(f"   Contraseña: admin123")
print(f"   ID: {admin.id}")

db.close()
