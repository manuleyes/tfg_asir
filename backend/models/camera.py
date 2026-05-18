"""
Modelo de Cámara
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from datetime import datetime
from models.database import Base


class Camera(Base):
    """
    Tabla de cámaras conectadas al sistema
    """
    __tablename__ = "cameras"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    location = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Camera {self.name}>"
