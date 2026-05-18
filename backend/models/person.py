"""
Modelo de Persona Detectada
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey
from datetime import datetime
from models.database import Base


class Person(Base):
    """
    Tabla de personas detectadas por el sistema
    """
    __tablename__ = "persons"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    person_id = Column(String(50), nullable=False)  # ID único de persona
    facial_features = Column(Text, nullable=True)  # Rasgos faciales
    confidence = Column(Float, default=0.0)  # Confianza de detección (0-1)
    times_detected = Column(Integer, default=1)  # Veces visto
    image_path = Column(String(500), nullable=True)  # Ruta de imagen
    detected_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Person {self.person_id}>"
