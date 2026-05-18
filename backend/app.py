"""
Aplicación FastAPI Principal - Sistema de Vigilancia Inteligente
"""
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
import os
import sys
import logging
from slowapi.errors import RateLimitExceeded
from slowapi import Limiter
from slowapi.util import get_remote_address

# Agregar ruta para importar módulos
sys.path.insert(0, os.path.dirname(__file__))

from config import get_settings
from models.database import engine, Base
from models import item as _item_model  # registrar DetectedItem en metadata
from routes import auth as auth_routes
from routes import cameras as cameras_routes
from routes import persons as persons_routes
from routes import vehicles as vehicles_routes
from routes import alerts as alerts_routes
from routes import detection as detection_routes
from routes import video as video_routes
from routes import analysis as analysis_routes
from routes import reports as reports_routes
from routes import ai_routes
from routes import camera_web_client
from routes import websocket_routes
from routes import export_routes
from routes import twofa_routes
from routes import email_routes
from routes import timeline_routes
from routes import database_routes
from middleware.session_middleware import SessionValidationMiddleware
from services.cache import redis_cache, limiter

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Obtener configuración
settings = get_settings()

# Crear tablas en la BD si no existen
Base.metadata.create_all(bind=engine)

# Crear aplicación FastAPI — docs deshabilitados en la raíz (se sirven manualmente con auth)
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Sistema de vigilancia inteligente con detección de personas y vehículos",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

#  MIDDLEWARE: Rate Limiting (primero)
app.state.limiter = limiter
from fastapi.responses import JSONResponse
app.add_exception_handler(RateLimitExceeded, lambda request, exc: JSONResponse(
    status_code=429,
    content={"error": "Rate limit exceeded", "detail": str(exc.detail)}
))

#  MIDDLEWARE: CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#  MIDDLEWARE: Validación de sesiones
app.add_middleware(SessionValidationMiddleware)

# Incluir rutas
app.include_router(auth_routes.router)
app.include_router(cameras_routes.router)
app.include_router(persons_routes.router)
app.include_router(vehicles_routes.router)
app.include_router(alerts_routes.router)
app.include_router(detection_routes.router)
app.include_router(video_routes.router)
app.include_router(analysis_routes.router)
app.include_router(reports_routes.router)
app.include_router(ai_routes.router)
app.include_router(camera_web_client.router)
app.include_router(websocket_routes.router)
app.include_router(export_routes.router)
app.include_router(twofa_routes.router)
app.include_router(email_routes.router)
app.include_router(timeline_routes.router)
app.include_router(database_routes.router)

# Servir archivos estáticos del frontend
frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')

# Montar CSS en /static/css
css_path = os.path.join(frontend_path, 'css')
if os.path.exists(css_path):
    app.mount("/static/css", StaticFiles(directory=css_path), name="static_css")

# Montar JS en /static/js
js_path = os.path.join(frontend_path, 'js')
if os.path.exists(js_path):
    app.mount("/static/js", StaticFiles(directory=js_path), name="static_js")

# Montar imágenes en /static/img
img_path = os.path.join(frontend_path, 'img')
if os.path.exists(img_path):
    app.mount("/static/img", StaticFiles(directory=img_path), name="static_img")

# Montar carpeta de capturas en /images (frames guardados por cámaras)
images_capture_path = os.path.join(os.path.dirname(__file__), '..', 'images')
os.makedirs(images_capture_path, exist_ok=True)
app.mount("/images", StaticFiles(directory=images_capture_path), name="images_capture")


# ── Endpoint público: descargar certificado SSL para móviles ──────────────────
_CERT_FILE = os.path.join(os.path.dirname(__file__), "ssl", "cert.pem")

@app.get("/instalar-cert", include_in_schema=False)
async def serve_cert_page():
    """Página HTML con instrucciones + botón de descarga del certificado."""
    html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Instalar certificado SSL</title>
<style>
  body{font-family:sans-serif;max-width:480px;margin:40px auto;padding:20px;background:#f5f5f5}
  h2{color:#2c5aa0}
  .btn{display:block;width:100%;padding:16px;background:#2c5aa0;color:#fff;text-align:center;
       border-radius:10px;font-size:18px;text-decoration:none;margin:20px 0}
  .steps{background:#fff;border-radius:10px;padding:16px;margin-top:16px}
  .steps h3{margin-top:0;color:#444}
  ol{padding-left:20px;line-height:1.8}
  .note{font-size:12px;color:#888;margin-top:20px}
</style>
</head>
<body>
<h2>📱 Instalar certificado SSL</h2>
<p>Para acceder sin avisos de seguridad instala el certificado en tu dispositivo.</p>
<a class="btn" href="/instalar-cert/descarga">⬇️ Descargar certificado</a>
<div class="steps">
  <h3>Android</h3>
  <ol>
    <li>Descarga el archivo con el botón de arriba</li>
    <li>Ve a <b>Ajustes → Seguridad → Cifrado y credenciales → Instalar certificado</b></li>
    <li>Selecciona <b>Certificado de CA</b> y elige el archivo descargado</li>
    <li>Acepta la advertencia y ponle un nombre (ej: Vigilancia)</li>
  </ol>
</div>
<div class="steps" style="margin-top:12px">
  <h3>iPhone / iPad (iOS)</h3>
  <ol>
    <li>Descarga el archivo — iOS te preguntará si quieres instalarlo, pulsa <b>Permitir</b></li>
    <li>Ve a <b>Ajustes → General → VPN y gestión de dispositivos</b></li>
    <li>Pulsa el perfil <b>vigilancia.local</b> → <b>Instalar</b></li>
    <li>Ve a <b>Ajustes → General → Información → Ajustes de confianza de certificados</b></li>
    <li>Activa el interruptor del certificado <b>vigilancia.local</b></li>
  </ol>
</div>
<p class="note">Este certificado solo sirve para la red local de Vigilancia Inteligente.</p>
</body>
</html>"""
    return HTMLResponse(content=html)

@app.get("/instalar-cert/descarga", include_in_schema=False)
async def download_cert():
    """Descarga directa del archivo cert.pem con cabecera correcta para móviles."""
    if not os.path.exists(_CERT_FILE):
        raise HTTPException(status_code=404, detail="Certificado no encontrado")
    return FileResponse(
        path=_CERT_FILE,
        media_type="application/x-x509-ca-cert",
        filename="vigilancia.crt",
        headers={"Content-Disposition": "attachment; filename=vigilancia.crt"}
    )


#  FUNCIÓN HELPER: Verificar sesión
def check_session_and_serve(request, file_path, redirect_to_login=True):
    """
    Verifica sesión válida antes de servir un archivo
    Si no hay sesión y redirect_to_login=True, redirige a /login
    
    Args:
        request: FastAPI Request
        file_path: Ruta del archivo a servir
        redirect_to_login: Si True, redirige a /login si no hay sesión
        
    Returns:
        FileResponse con el archivo o RedirectResponse a /login
    """
    from auth.session_handler import SESSION_COOKIE_NAME, validate_session_cookie
    from itsdangerous import BadSignature, SignatureExpired
    
    # Obtener cookie de sesión
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    session_valid = False
    
    if session_cookie:
        try:
            session_data = validate_session_cookie(session_cookie)
            session_valid = True
        except (BadSignature, SignatureExpired):
            session_valid = False
    
    # Si sesión no es válida y debe redirigir
    if not session_valid and redirect_to_login:
        #  Redirigir SIEMPRE a /login
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Si sesión es válida o no requiere redirección, servir archivo
    if os.path.exists(file_path):
        return FileResponse(file_path)
    
    return HTMLResponse(status_code=404, content={"message": "Archivo no encontrado"})


# Ruta raíz: Siempre redirige a login o dashboard según sesión
@app.get("/", include_in_schema=False)
async def serve_root(request: Request):
    """
    Raíz: Redirige según estado de autenticación
    - Con sesión válida → /dashboard
    - Sin sesión → /login
    """
    from auth.session_handler import SESSION_COOKIE_NAME, validate_session_cookie
    from itsdangerous import BadSignature, SignatureExpired
    
    try:
        # Obtener cookie de sesión
        session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
        
        # Si hay cookie, intentar validarla
        if session_cookie:
            try:
                session_data = validate_session_cookie(session_cookie)
                # Sesión válida → ir al dashboard
                logger.info("Valid session detected, redirecting to dashboard")
                return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
            except (BadSignature, SignatureExpired):
                # Cookie inválida o expirada → login
                logger.info("Invalid or expired session, redirecting to login")
                return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        
        # Sin cookie → login
        logger.info("No session cookie found, redirecting to login")
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        
    except Exception as e:
        # En caso de error inesperado, ir a login (opción segura)
        logger.error(f"Error in root route: {str(e)}")
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


# Ruta /login: Sirve el formulario de login
@app.get("/login", include_in_schema=False)
async def serve_login(request: Request):
    """Página de login - Sirve formulario"""
    #  Rechazar si hay parámetros GET (seguridad)
    if request.query_params:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Servir login
    login_file = os.path.join(frontend_path, 'html', 'index.html')
    if os.path.exists(login_file):
        return FileResponse(login_file)
    return {"message": "Frontend no disponible"}


# Redirecciones de rutas .html a rutas limpias
@app.get("/dashboard.html", include_in_schema=False)
async def redirect_dashboard_html():
    """Redirigir /dashboard.html a /dashboard"""
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_301_MOVED_PERMANENTLY)

@app.get("/camaras.html", include_in_schema=False)
async def redirect_camaras_html():
    """Redirigir /camaras.html a /camaras"""
    return RedirectResponse(url="/camaras", status_code=status.HTTP_301_MOVED_PERMANENTLY)

@app.get("/personas.html", include_in_schema=False)
async def redirect_personas_html():
    """Redirigir /personas.html a /personas"""
    return RedirectResponse(url="/personas", status_code=status.HTTP_301_MOVED_PERMANENTLY)

@app.get("/vehiculos.html", include_in_schema=False)
async def redirect_vehiculos_html():
    """Redirigir /vehiculos.html a /vehiculos"""
    return RedirectResponse(url="/vehiculos", status_code=status.HTTP_301_MOVED_PERMANENTLY)

@app.get("/alertas.html", include_in_schema=False)
async def redirect_alertas_html():
    """Redirigir /alertas.html a /alertas"""
    return RedirectResponse(url="/alertas", status_code=status.HTTP_301_MOVED_PERMANENTLY)

@app.get("/bd.html", include_in_schema=False)
async def redirect_bd_html():
    """Redirigir /bd.html a /bd"""
    return RedirectResponse(url="/bd", status_code=status.HTTP_301_MOVED_PERMANENTLY)

@app.get("/reportes.html", include_in_schema=False)
async def redirect_reportes_html():
    """Redirigir /reportes.html a /reportes"""
    return RedirectResponse(url="/reportes", status_code=status.HTTP_301_MOVED_PERMANENTLY)

@app.get("/live-detection.html", include_in_schema=False)
async def redirect_live_detection_html():
    """Redirigir /live-detection.html a /live-detection"""
    return RedirectResponse(url="/live-detection", status_code=status.HTTP_301_MOVED_PERMANENTLY)

@app.get("/diagnostico.html", include_in_schema=False)
async def redirect_diagnostico_html():
    """Redirigir /diagnostico.html a /diagnostico"""
    return RedirectResponse(url="/diagnostico", status_code=status.HTTP_301_MOVED_PERMANENTLY)

# Helper para verificar sesión y servir dashboard con diferentes rutas
async def _serve_dashboard_page(request: Request):
    """Servir dashboard.html con sesión válida"""
    from auth.session_handler import SESSION_COOKIE_NAME, validate_session_cookie
    from itsdangerous import BadSignature, SignatureExpired
    
    dashboard_file = os.path.join(frontend_path, 'html', 'dashboard.html')
    
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    session_valid = False
    
    if session_cookie:
        try:
            session_data = validate_session_cookie(session_cookie)
            session_valid = True
        except (BadSignature, SignatureExpired):
            session_valid = False
    
    if not session_valid:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    if os.path.exists(dashboard_file):
        return FileResponse(dashboard_file)
    return HTMLResponse(status_code=404, content={"message": "Archivo no encontrado"})


# Rutas del Dashboard sin hash (#)
@app.get("/dashboard", include_in_schema=False)
async def serve_dashboard(request: Request):
    """Página principal del dashboard"""
    return await _serve_dashboard_page(request)

@app.get("/camaras", include_in_schema=False)
async def serve_camaras(request: Request):
    """Página de cámaras"""
    return await _serve_dashboard_page(request)

@app.get("/personas", include_in_schema=False)
async def serve_personas(request: Request):
    """Página de personas detectadas (redirige a detecciones)"""
    return await _serve_dashboard_page(request)

@app.get("/vehiculos", include_in_schema=False)
async def serve_vehiculos(request: Request):
    """Página de vehículos detectados (redirige a detecciones)"""
    return await _serve_dashboard_page(request)

@app.get("/detecciones", include_in_schema=False)
async def serve_detecciones(request: Request):
    """Página unificada de detecciones"""
    return await _serve_dashboard_page(request)

@app.get("/alertas", include_in_schema=False)
async def serve_alertas(request: Request):
    """Página de alertas"""
    return await _serve_dashboard_page(request)

@app.get("/bd", include_in_schema=False)
async def serve_bd(request: Request):
    """Página de base de datos"""
    return await _serve_dashboard_page(request)

@app.get("/reportes", include_in_schema=False)
async def serve_reportes(request: Request):
    """Página de reportes"""
    return await _serve_dashboard_page(request)

@app.get("/live-detection", include_in_schema=False)
async def serve_live_detection_clean(request: Request):
    """Página de detección en vivo (limpia, sin .html)"""
    return await _serve_dashboard_page(request)

@app.get("/diagnostico", include_in_schema=False)
async def serve_diagnostico_clean(request: Request):
    """Página de diagnóstico (limpia, sin .html)"""
    return await _serve_dashboard_page(request)

@app.get("/live-detection.html", include_in_schema=False)
async def serve_live_detection(request: Request):
    """Redirigir /live-detection.html a /live-detection (duplicada por seguridad)"""
    return RedirectResponse(url="/live-detection", status_code=status.HTTP_301_MOVED_PERMANENTLY)

@app.get("/diagnostico.html", include_in_schema=False)
async def serve_diagnostico(request: Request):
    """Redirigir /diagnostico.html a /diagnostico (duplicada por seguridad)"""
    return RedirectResponse(url="/diagnostico", status_code=status.HTTP_301_MOVED_PERMANENTLY)

@app.get("/index.html", include_in_schema=False)
async def serve_login_html():
    """Redirigir /index.html a /login"""
    return RedirectResponse(url="/login", status_code=status.HTTP_301_MOVED_PERMANENTLY)

@app.get("/perfil", include_in_schema=False)
async def serve_perfil(request: Request):
    """Página de edición de perfil de usuario"""
    from auth.session_handler import SESSION_COOKIE_NAME, validate_session_cookie
    from itsdangerous import BadSignature, SignatureExpired
    
    perfil_file = os.path.join(frontend_path, 'html', 'perfil.html')
    
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    session_valid = False
    
    if session_cookie:
        try:
            session_data = validate_session_cookie(session_cookie)
            session_valid = True
        except (BadSignature, SignatureExpired):
            session_valid = False
    
    if not session_valid:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    if os.path.exists(perfil_file):
        return FileResponse(perfil_file)
    return HTMLResponse(status_code=404, content={"message": "Archivo no encontrado"})


@app.get("/timeline", include_in_schema=False)
async def serve_timeline(request: Request):
    """Página de línea temporal de eventos"""
    return await _serve_dashboard_page(request)


@app.get("/camara-cliente", include_in_schema=False)
async def serve_camara_cliente(request: Request):
    """Página cliente de cámara (móvil/portátil) — accesible sin sesión para facilitar conexión"""
    camara_file = os.path.join(frontend_path, 'html', 'camara-cliente.html')
    if os.path.exists(camara_file):
        return FileResponse(camara_file)
    return HTMLResponse(status_code=404, content="Archivo no encontrado")


# Rutas básicas
@app.get("/api/health")
def health_check():
    """Health check del sistema"""
    return {
        "status": "ok",
        "cache": "connected" if redis_cache.is_available() else "disconnected"
    }


@app.get("/api/server-ips")
def get_server_ips():
    """
    Obtener IPs públicas y locales del servidor
    """
    try:
        from utils.ip_utils import get_server_ips as get_ips
        ips = get_ips()
        return {
            "success":   True,
            "local_ip":  ips.get("local", "127.0.0.1"),
            "public_ip": ips.get("public"),
            "port":      ips.get("port", "16000"),
            "protocol":  ips.get("protocol", "http"),
        }
    except Exception as e:
        logger.error(f"Error obteniendo IPs: {e}")
        return {
            "success":   False,
            "error":     str(e),
            "local_ip":  "127.0.0.1",
            "public_ip": None,
            "port":      "16000",
            "protocol":  "http",
        }


@app.get("/api/dashboard")
def get_dashboard_info():
    """
    Endpoint de dashboard (placeholder)
    Información general del sistema
    """
    return {
        "system_status": "online",
        "cameras_connected": 0,
        "persons_detected": 0,
        "vehicles_detected": 0,
        "active_alerts": 0
    }


@app.on_event("startup")
async def migrate_to_detected_items():
    """Migrar registros históricos de persons/vehicles a detected_items si la tabla está vacía."""
    try:
        from models.database import SessionLocal
        from models.item import DetectedItem
        from models.person import Person
        from models.vehicle import Vehicle
        from datetime import datetime

        db = SessionLocal()
        try:
            count = db.query(DetectedItem).count()
            if count == 0:
                migrated = 0
                for p in db.query(Person).all():
                    db.add(DetectedItem(
                        camera_id=p.camera_id,
                        item_id=p.person_id or f"person_{p.id}",
                        type='person',
                        label=p.person_id or f"person_{p.id}",
                        confidence=p.confidence or 0.0,
                        times_detected=p.times_detected or 1,
                        image_path=p.image_path,
                        detected_at=p.detected_at or datetime.utcnow(),
                        created_at=p.created_at or datetime.utcnow(),
                    ))
                    migrated += 1
                for v in db.query(Vehicle).all():
                    lbl = ' '.join(filter(None, [v.vehicle_model, v.vehicle_color])) or f"vehicle_{v.id}"
                    db.add(DetectedItem(
                        camera_id=v.camera_id,
                        item_id=v.license_plate or f"vehicle_{v.id}",
                        type='vehicle',
                        label=lbl,
                        confidence=v.confidence or 0.0,
                        times_detected=v.times_detected or 1,
                        image_path=v.image_path,
                        detected_at=v.detected_at or datetime.utcnow(),
                        created_at=v.created_at or datetime.utcnow(),
                    ))
                    migrated += 1
                if migrated:
                    db.commit()
                    logger.info(f"Migración detected_items: {migrated} registros copiados")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error en migración detected_items: {e}")


@app.on_event("startup")
async def detect_public_ip():
    """Detectar IP pública real al arrancar y actualizar settings"""
    import asyncio
    from utils.ip_utils import get_public_ip
    try:
        loop = asyncio.get_event_loop()
        ip = await loop.run_in_executor(None, get_public_ip)
        if ip:
            settings.public_ip = ip
            logger.info(f"IP pública detectada automáticamente: {ip}")
        else:
            logger.warning("No se pudo detectar IP pública, usando valor por defecto")
    except Exception as e:
        logger.error(f"Error detectando IP pública en startup: {e}")


# --- Swagger UI protegido por sesión ---
def _is_session_valid(request: Request) -> bool:
    from auth.session_handler import SESSION_COOKIE_NAME, validate_session_cookie
    from itsdangerous import BadSignature, SignatureExpired
    cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if not cookie:
        return False
    try:
        validate_session_cookie(cookie)
        return True
    except (BadSignature, SignatureExpired):
        return False


@app.get("/api/openapi.json", include_in_schema=False)
async def get_openapi(request: Request):
    if not _is_session_valid(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    from fastapi.openapi.utils import get_openapi as _get_openapi
    return _get_openapi(
        title=settings.api_title,
        version=settings.api_version,
        routes=app.routes,
    )


@app.get("/api/docs", include_in_schema=False)
async def get_docs(request: Request):
    if not _is_session_valid(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    from fastapi.openapi.docs import get_swagger_ui_html
    return get_swagger_ui_html(openapi_url="/api/openapi.json", title="API Docs")


@app.get("/api/redoc", include_in_schema=False)
async def get_redoc(request: Request):
    if not _is_session_valid(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    from fastapi.openapi.docs import get_redoc_html
    return get_redoc_html(openapi_url="/api/openapi.json", title="API ReDoc")


# Manejador de errores 404
@app.exception_handler(404)
async def not_found_exception_handler(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint no encontrado", "path": str(request.url.path)}
    )


# Manejador de errores 500
@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"error": "Error interno del servidor"}
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",  # nosec B104 - intentional: server binds all interfaces
        port=16000,
        reload=settings.debug,
        log_level="info"
    )
