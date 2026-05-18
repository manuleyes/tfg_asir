"""
Manejo de JWT (JSON Web Tokens)
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
from config import get_settings

settings = get_settings()


def create_access_token(data: dict, expires_in_hours: Optional[int] = None) -> str:
    """
    Crea un JWT token
    
    Args:
        data: Datos a incluir en el token (ej: {"sub": "username"})
        expires_in_hours: Horas hasta que expire (default: config)
        
    Returns:
        Token JWT codificado
    """
    to_encode = data.copy()
    
    if expires_in_hours is None:
        expires_in_hours = settings.jwt_expiration_hours
    
    expire = datetime.utcnow() + timedelta(hours=expires_in_hours)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict]:
    """
    Decodifica y valida un JWT token
    
    Args:
        token: Token JWT a validar
        
    Returns:
        Datos del token si es válido, None si no
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        print("Token expirado")
        return None
    except jwt.InvalidTokenError:
        print("Token inválido")
        return None
