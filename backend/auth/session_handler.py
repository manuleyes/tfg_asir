"""
session_handler.py - Manejo de sesiones con cookies firmadas
"""
from itsdangerous import TimestampSigner, BadSignature, SignatureExpired
from datetime import datetime, timedelta
import json
import os

from config import get_settings

settings = get_settings()

# Clave secreta para firmar cookies
SESSION_SECRET_KEY = settings.session_secret_key
SESSION_EXPIRATION_HOURS = settings.session_expiration_hours
SESSION_COOKIE_NAME = 'vigilancia_session'

signer = TimestampSigner(SESSION_SECRET_KEY)


class SessionData:
    """Estructura de datos de sesión"""
    def __init__(self, user_id: int, username: str, is_admin: bool):
        self.user_id = user_id
        self.username = username
        self.is_admin = is_admin
        self.created_at = datetime.utcnow().isoformat()
        self.expires_at = (datetime.utcnow() + timedelta(hours=SESSION_EXPIRATION_HOURS)).isoformat()

    def to_dict(self):
        """Convertir a diccionario"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'is_admin': self.is_admin,
            'created_at': self.created_at,
            'expires_at': self.expires_at
        }

    @staticmethod
    def from_dict(data: dict):
        """Crear desde diccionario"""
        session = SessionData(
            user_id=data['user_id'],
            username=data['username'],
            is_admin=data['is_admin']
        )
        session.created_at = data['created_at']
        session.expires_at = data['expires_at']
        return session


def create_session_cookie(user_id: int, username: str, is_admin: bool = False) -> str:
    """
    Crear una cookie de sesión firmada
    
    Args:
        user_id: ID del usuario
        username: Nombre del usuario
        is_admin: Si es administrador
        
    Returns:
        Cookie value firmada
    """
    session_data = SessionData(user_id, username, is_admin)
    json_data = json.dumps(session_data.to_dict())
    signed_data = signer.sign(json_data)
    return signed_data.decode() if isinstance(signed_data, bytes) else signed_data


def validate_session_cookie(cookie_value: str, max_age_hours: int = None) -> dict:
    """
    Validar y decodificar una cookie de sesión
    
    Args:
        cookie_value: Valor de la cookie
        max_age_hours: Máxima edad permitida (en horas)
        
    Returns:
        dict con datos de sesión si es válida
        
    Raises:
        BadSignature: Si la firma es inválida
        SignatureExpired: Si la cookie expiró
    """
    if max_age_hours is None:
        max_age_hours = SESSION_EXPIRATION_HOURS
    
    max_age_seconds = max_age_hours * 3600
    
    try:
        json_data = signer.unsign(cookie_value, max_age=max_age_seconds)
        data = json.loads(json_data)
        
        # Verificar expiración adicional
        expires_at = datetime.fromisoformat(data['expires_at'])
        if datetime.utcnow() > expires_at:
            raise SignatureExpired("Session has expired")
        
        return data
    except BadSignature:
        raise BadSignature("Invalid session signature")
    except SignatureExpired:
        raise SignatureExpired("Session has expired")


def get_session_from_cookie(cookie_value: str) -> SessionData:
    """
    Obtener objeto SessionData desde cookie
    
    Args:
        cookie_value: Valor de la cookie
        
    Returns:
        SessionData instance
    """
    data = validate_session_cookie(cookie_value)
    return SessionData.from_dict(data)
