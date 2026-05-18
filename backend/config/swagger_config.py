"""
Swagger/OpenAPI Documentation Configuration
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def configure_openapi(app: FastAPI):
    """
    Configurar OpenAPI/Swagger personalizado
    """
    
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title="Sistema de Vigilancia Inteligente - API",
            version="1.0.0",
            description="""
            # 🎥 API de Vigilancia Inteligente
            
            Sistema avanzado de vigilancia con detección en tiempo real de personas y vehículos.
            
            ##  Características
            -  Autenticación JWT + Cookies
            -  Detección YOLO en tiempo real
            -  Caché Redis (100x más rápido)
            -  Rate limiting (protección contra abuse)
            -  Reportes PDF/CSV/JSON
            -  WebSocket para streaming
            
            ## 🔐 Autenticación
            Todos los endpoints requieren JWT token:
            ```
            Authorization: Bearer {token}
            ```
            
            ## 📊 Rate Limits
            - Default: 100 requests/minuto
            - Auth: 10 requests/minuto
            - Detección: 50 requests/minuto
            - Exportación: 20 requests/minuto
            
            ## 💾 Endpoints Principales
            - `/api/auth/*` - Autenticación
            - `/api/camaras/*` - Gestión de cámaras
            - `/api/personas/*` - Historial de personas
            - `/api/vehiculos/*` - Historial de vehículos
            - `/api/deteccion/*` - Detecciones
            - `/api/reportes/*` - Reportes
            """,
            contact={
                "name": "Sistema de Vigilancia",
                "email": "admin@vigilancia.local"
            },
            routes=app.routes,
        )
        
        # Personalizar esquema
        openapi_schema["info"]["x-logo"] = {
            "url": "https://fastapi.tiangolo.com/img/favicon.png"
        }
        
        # Agregar servidor
        openapi_schema["servers"] = [
            {"url": "http://localhost:8000", "description": "Desarrollo"},
            {"url": "https://api.vigilancia.com", "description": "Producción"}
        ]
        
        # Agregar ejemplos de respuesta
        if "components" in openapi_schema:
            openapi_schema["components"]["schemas"]["PersonResponse"] = {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "camera_id": {"type": "integer"},
                    "times_seen": {"type": "integer"},
                    "last_seen": {"type": "string"}
                },
                "example": {
                    "id": 1,
                    "camera_id": 1,
                    "times_seen": 5,
                    "last_seen": "2024-01-15T10:30:00"
                }
            }
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi


# ============ SWAGGER UI PERSONALIZADO ============
swagger_ui_parameters = {
    "apisSorter": "alpha",
    "operationsSorter": "alpha",
    "docExpansion": "list",
    "defaultModelsExpandDepth": 1,
    "displayOperationId": True,
}

# Ejemplo de uso en app.py:
# app.swagger_ui_parameters = swagger_ui_parameters
# configure_openapi(app)
