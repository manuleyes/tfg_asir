"""
Configuración de Base de Datos MySQL con SQLAlchemy
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import get_settings

settings = get_settings()

# URL de conexión
DATABASE_URL = settings.database_url

# Crear motor de conexión
engine = create_engine(
    DATABASE_URL,
    echo=settings.debug,  # Log de queries SQL
    pool_pre_ping=True,   # Verifica conexión antes de usar
    pool_size=10,
    max_overflow=20
)

# Sesión maker
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base para modelos
Base = declarative_base()


def get_db():
    """
    Dependency para inyectar sesión de BD en rutas
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
