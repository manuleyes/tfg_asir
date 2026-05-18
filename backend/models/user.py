"""
Modelo de Usuario (Admin)
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum
from datetime import datetime
from models.database import Base
import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    operator = "operator"
    viewer = "viewer"


class User(Base):
    """
    Tabla de usuarios administrativos
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    role = Column(String(20), default=UserRole.admin, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=True)
    # 2FA
    totp_secret = Column(String(64), nullable=True)
    totp_enabled = Column(Boolean, default=False)
    # Contact
    phone = Column(String(30), nullable=True)
    # Email notifications
    email_notifications = Column(Boolean, default=False)
    notify_critical = Column(Boolean, default=True)
    notify_warning = Column(Boolean, default=False)
    # Phone/SMS notifications
    phone_notifications = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username}>"
