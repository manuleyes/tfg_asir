"""
Configuración del proyecto - Lee variables de .env
Soporta MySQL y SQLite
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """
    Configuración de la aplicación
    Lee desde fichero .env
    """
    
    # BD Config
    database_type: str = "sqlite"  # "sqlite" o "mysql"
    
    # MySQL config (si usa MySQL)
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "vigilancia_db"
    
    # SQLite config (si usa SQLite)
    sqlite_path: str = "./vigilancia.db"
    
    # JWT
    jwt_secret_key: str = "tu_super_secret_key_cambiar_en_produccion_2024"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Session (Cookies)
    session_secret_key: str = "tu_session_secret_key_cambiar_en_produccion_2024"
    session_expiration_hours: int = 24
    
    # FastAPI
    api_title: str = "Sistema de Vigilancia Inteligente"
    api_version: str = "1.0.0"
    debug: bool = True
    
    # Network Config para clientes remotos
    public_ip: str = "81.61.2.97"   # IP pública (DNAT en router)
    public_port: int = 16000         # Puerto HTTP público (DNAT 16000->16000)
    public_https_port: int = 16443   # Puerto HTTPS público (DNAT 16443->16443)
    router_port: int = 16000         # Puerto del router (si es diferente del public_port)
    local_ip: str = "localhost"      # IP local para desarrollo

    # Email / SMTP (opcional)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    alert_email_to: str = ""  # destinatarios de alertas, separados por coma

    model_config = {"extra": "allow", "env_file": ".env", "case_sensitive": False}
    
    @property
    def database_url(self) -> str:
        """URL de conexión según tipo de BD"""
        if self.database_type == "mysql":
            return f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        else:  # SQLite
            return f"sqlite:///{self.sqlite_path}"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
