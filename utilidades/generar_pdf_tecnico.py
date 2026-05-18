"""
Script para generar documentación técnica en PDF profesional
Utiliza ReportLab para maquetación de alta calidad
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib import colors
from datetime import datetime
import os

def generar_pdf_tecnico():
    """Genera documento PDF técnico profesional"""
    
    # Configuración
    filename = "DOCUMENTACION_TECNICA_SISTEMA_VIGILANCIA.pdf"
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
        title="Documentación Técnica - Sistema de Vigilancia Inteligente"
    )
    
    # Estilos personalizados
    styles = getSampleStyleSheet()
    
    style_titulo_principal = ParagraphStyle(
        'TituloPrincipal',
        parent=styles['Heading1'],
        fontSize=36,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    style_titulo_seccion = ParagraphStyle(
        'TituloSeccion',
        parent=styles['Heading2'],
        fontSize=20,
        textColor=colors.HexColor('#2e5f9e'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold',
        borderPadding=10,
        borderColor=colors.HexColor('#2e5f9e'),
        borderWidth=0,
    )
    
    style_titulo_subseccion = ParagraphStyle(
        'TituloSubseccion',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=colors.HexColor('#3d7ab9'),
        spaceAfter=8,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    style_texto = ParagraphStyle(
        'TextoNormal',
        parent=styles['BodyText'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
        fontName='Helvetica',
        textColor=colors.HexColor('#333333')
    )
    
    style_codigo = ParagraphStyle(
        'Codigo',
        parent=styles['BodyText'],
        fontSize=9,
        alignment=TA_LEFT,
        spaceAfter=8,
        fontName='Courier',
        textColor=colors.HexColor('#1a1a1a'),
        leftIndent=20,
        backColor=colors.HexColor('#f5f5f5')
    )
    
    # Contenido
    contenido = []
    
    # ============== PORTADA ==============
    contenido.append(Spacer(1, 1.5*inch))
    
    contenido.append(Paragraph(
        "SISTEMA DE VIGILANCIA INTELIGENTE",
        style_titulo_principal
    ))
    
    contenido.append(Spacer(1, 0.3*inch))
    
    contenido.append(Paragraph(
        "Documentación Técnica Completa v1.0.0",
        ParagraphStyle('Subtitulo', parent=styles['Normal'], fontSize=16, alignment=TA_CENTER, textColor=colors.HexColor('#2e5f9e'))
    ))
    
    contenido.append(Spacer(1, 0.3*inch))
    
    contenido.append(Paragraph(
        "Proyecto Final ASIR<br/>Detección en Tiempo Real con IA",
        ParagraphStyle('Descripcion', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER, textColor=colors.HexColor('#555555'))
    ))
    
    contenido.append(Spacer(1, 1*inch))
    
    info_portada = f"""
    <font face="Helvetica" size="11">
    <b>Fecha:</b> Abril 2026<br/>
    <b>Versión:</b> 1.0.0<br/>
    <b>Estado:</b> Completada<br/>
    <b>Autor:</b> Proyecto Final ASIR
    </font>
    """
    
    contenido.append(Paragraph(
        info_portada,
        ParagraphStyle('Info', parent=styles['Normal'], fontSize=11, alignment=TA_CENTER)
    ))
    
    contenido.append(PageBreak())
    
    # ============== TABLA DE CONTENIDOS ==============
    contenido.append(Paragraph("Tabla de Contenidos", style_titulo_seccion))
    contenido.append(Spacer(1, 0.2*inch))
    
    toc_items = [
        "1. Descripción General",
        "2. Stack Tecnológico",
        "3. Arquitectura del Sistema",
        "4. Componentes Principales",
        "5. Modelos de Datos",
        "6. Endpoints API REST",
        "7. Servicios Implementados",
        "8. Seguridad y Autenticación",
        "9. Instalación y Configuración",
        "10. Deployment",
        "11. Características Implementadas",
        "12. Requisitos del Sistema"
    ]
    
    for item in toc_items:
        contenido.append(Paragraph(item, style_texto))
        contenido.append(Spacer(1, 0.08*inch))
    
    contenido.append(PageBreak())
    
    # ============== 1. DESCRIPCION GENERAL ==============
    contenido.append(Paragraph("1. Descripción General", style_titulo_seccion))
    
    contenido.append(Paragraph(
        "Sistema de monitoreo y vigilancia inteligente para detección en tiempo real de personas y vehículos mediante visión por computadora (YOLO v8). El sistema integra múltiples componentes de software moderno para proporcionar una solución completa de vigilancia con inteligencia artificial integrada.",
        style_texto
    ))
    
    contenido.append(Spacer(1, 0.15*inch))
    contenido.append(Paragraph("Componentes Principales:", style_titulo_subseccion))
    
    caracteristicas = """
    • Captura de video en tiempo real desde cámaras locales y remotas (RTSP)<br/>
    • Procesamiento de frames con modelo YOLOv8-XLarge<br/>
    • Almacenamiento de detecciones en base de datos relacional<br/>
    • Dashboard web con autenticación JWT<br/>
    • Sistema de alertas basado en eventos<br/>
    • Generación de reportes en PDF<br/>
    • API REST completa para integración de terceros
    """
    
    contenido.append(Paragraph(caracteristicas, style_texto))
    
    contenido.append(Spacer(1, 0.15*inch))
    contenido.append(Paragraph("Objetivo del Proyecto:", style_titulo_subseccion))
    
    contenido.append(Paragraph(
        "Proporcionar una solución escalable de vigilancia con IA integrada, segura y fácil de desplegar en entornos locales o en la nube, permitiendo la detección automática de personas y vehículos con análisis histórico y generación de reportes.",
        style_texto
    ))
    
    contenido.append(PageBreak())
    
    # ============== 2. STACK TECNOLOGICO ==============
    contenido.append(Paragraph("2. Stack Tecnológico", style_titulo_seccion))
    
    seccion_backend = """
    <b>Backend</b><br/>
    Framework: FastAPI 0.104.1 (async, OpenAPI/Swagger)<br/>
    Servidor Web: Uvicorn 0.24.0 (ASGI)<br/>
    ORM: SQLAlchemy 2.0.23 (con pool de conexiones)<br/>
    Validación: Pydantic 2.5.0 (schemas, type hints)
    """
    
    contenido.append(Paragraph(seccion_backend, style_texto))
    contenido.append(Spacer(1, 0.1*inch))
    
    seccion_auth = """
    <b>Autenticación y Seguridad</b><br/>
    JWT: PyJWT 2.8.0 (HS256)<br/>
    Hash Contraseñas: Bcrypt 4.1.1 (12 rounds)<br/>
    Rate Limiting: SlowAPI 0.1.9<br/>
    CORS: Implementado en middleware
    """
    
    contenido.append(Paragraph(seccion_auth, style_texto))
    contenido.append(Spacer(1, 0.1*inch))
    
    seccion_ia = """
    <b>Inteligencia Artificial y Visión</b><br/>
    Detección: YOLOv8-XLarge (Ultralytics 8.0.234)<br/>
    Procesamiento: OpenCV 4.8.1.78<br/>
    Backend ML: PyTorch 2.6.0 + CPU optimization<br/>
    Reconocimiento Facial: DeepFace 0.0.75<br/>
    ML Utils: Scikit-learn 1.3.2, NumPy 1.24.3
    """
    
    contenido.append(Paragraph(seccion_ia, style_texto))
    contenido.append(Spacer(1, 0.1*inch))
    
    seccion_bd = """
    <b>Base de Datos</b><br/>
    Relacional: MySQL 8.0+ (producción) / SQLite 3 (desarrollo)<br/>
    Driver MySQL: PyMySQL 1.1.0<br/>
    Session Manager: Redis 5.0.1 (caché, tokenización)
    """
    
    contenido.append(Paragraph(seccion_bd, style_texto))
    contenido.append(Spacer(1, 0.1*inch))
    
    seccion_reportes = """
    <b>Reportes y Exportación</b><br/>
    PDF: ReportLab 4.4.10<br/>
    Gráficos: Matplotlib (opcional)<br/>
    Serialización: JSON nativo Python
    """
    
    contenido.append(Paragraph(seccion_reportes, style_texto))
    contenido.append(Spacer(1, 0.1*inch))
    
    seccion_infra = """
    <b>Infraestructura</b><br/>
    Containerización: Docker + Docker Compose<br/>
    Python: 3.9+ (compatible con 3.11)<br/>
    Gestor Paquetes: pip
    """
    
    contenido.append(Paragraph(seccion_infra, style_texto))
    
    contenido.append(PageBreak())
    
    # ============== 3. ARQUITECTURA ==============
    contenido.append(Paragraph("3. Arquitectura del Sistema", style_titulo_seccion))
    
    contenido.append(Paragraph("Patrón de Arquitectura: Arquitectura de Capas (Layered Architecture)", style_titulo_subseccion))
    
    contenido.append(Paragraph(
        "El sistema está organizado en capas verticales independientes que permiten escalabilidad, mantenibilidad y separación de responsabilidades.",
        style_texto
    ))
    
    contenido.append(Spacer(1, 0.1*inch))
    
    arch_layers = """
    <b>Capa de Presentación (Frontend)</b><br/>
    HTML5 + CSS3 + JavaScript Vanilla. Dashboard responsivo sin dependencias externas de frameworks pesados.<br/>
    <br/>
    <b>Capa API (FastAPI)</b><br/>
    14 routers independientes: auth, cameras, detection, analysis, reports, video, alerts, ai, etc.<br/>
    <br/>
    <b>Middleware</b><br/>
    Validación JWT, CORS, Rate Limiting, Session Management, Error Handling.<br/>
    <br/>
    <b>Capa de Negocio (Services)</b><br/>
    DetectionService, ReportService, VideoProcessor, AlertService, CacheService, AuthService.<br/>
    <br/>
    <b>Capa de Datos (Data Access)</b><br/>
    SQLAlchemy ORM, Modelos (User, Camera, Person, Vehicle, Alert, Detection), Connection Pooling.<br/>
    <br/>
    <b>Persistencia</b><br/>
    MySQL (producción) / SQLite (desarrollo).
    """
    
    contenido.append(Paragraph(arch_layers, style_texto))
    
    contenido.append(PageBreak())
    
    # ============== 4. COMPONENTES PRINCIPALES ==============
    contenido.append(Paragraph("4. Componentes Principales", style_titulo_seccion))
    
    contenido.append(Paragraph("Backend - Estructura de Directorios", style_titulo_subseccion))
    
    backend_struct = """
    <b>app.py</b> - Aplicación FastAPI principal con middleware y registro de routers<br/>
    <br/>
    <b>config.py</b> - Configuración centralizada con Pydantic Settings<br/>
    <br/>
    <b>auth/</b> - Autenticación (JWT, Bcrypt, Session Manager)<br/>
    <br/>
    <b>models/</b> - SQLAlchemy ORM models (User, Camera, Person, Vehicle, Alert, Detection)<br/>
    <br/>
    <b>routes/</b> - 14 routers API (auth, cameras, persons, vehicles, detection, video, analysis, reports, alerts, ai, etc)<br/>
    <br/>
    <b>middleware/</b> - Validación JWT, Session Management, Error Handling<br/>
    <br/>
    <b>services/</b> - Lógica de negocio (Detection, Reports, Cache, Auth, VideoProcessor, FaceRecognition, BehaviorPredictor)
    """
    
    contenido.append(Paragraph(backend_struct, style_texto))
    
    contenido.append(Spacer(1, 0.15*inch))
    
    contenido.append(Paragraph("Frontend - Estructura", style_titulo_subseccion))
    
    frontend_struct = """
    <b>index.html</b> - Página de login<br/>
    <b>dashboard.html</b> - Panel principal de monitoreo<br/>
    <b>diagnostico.html</b> - Herramientas de diagnóstico<br/>
    <b>css/</b> - Estilos responsivos (Grid/Flexbox)<br/>
    <b>js/</b> - Lógica interactiva, WebSocket, gráficos<br/>
    <b>pages/</b> - Páginas específicas (cámaras, reportes, alertas)
    """
    
    contenido.append(Paragraph(frontend_struct, style_texto))
    
    contenido.append(Spacer(1, 0.15*inch))
    
    contenido.append(Paragraph("Cliente - Módulos Python", style_titulo_subseccion))
    
    cliente_struct = """
    <b>camera_streaming_client.py</b> - Captura de video, compresión, envío UDP<br/>
    <b>config.py</b> - Configuración del cliente (servidor, codec, resolución)<br/>
    <b>multi_camera.py</b> - Soporte para múltiples cámaras con threading<br/>
    <b>demo.py</b> - Script de demostración
    """
    
    contenido.append(Paragraph(cliente_struct, style_texto))
    
    contenido.append(PageBreak())
    
    # ============== 5. MODELOS DE DATOS ==============
    contenido.append(Paragraph("5. Modelos de Datos", style_titulo_seccion))
    
    contenido.append(Paragraph("Schema de Base de Datos Relacional", style_titulo_subseccion))
    
    tabla_schema = [
        ["Tabla", "Campos Principales", "Índices"],
        ["users", "id, username, password_hash, email, is_active, is_admin, created_at, updated_at", "username, email"],
        ["cameras", "id, camera_id, name, location, camera_source, resolution, fps, codec, is_active, last_heartbeat", "camera_id, is_active"],
        ["persons", "id, camera_id, detection_count, last_seen, facial_features (JSON), confidence_score, is_tracked", "camera_id, is_tracked"],
        ["vehicles", "id, camera_id, vehicle_type, plate_number, detection_count, last_seen, color, confidence_score", "camera_id, plate_number"],
        ["detections", "id, camera_id, frame_number, timestamp, class_name, confidence, bbox_coords (JSON), image_path", "camera_id, timestamp, class_name"],
        ["alerts", "id, camera_id, detection_id, alert_type, severity (1-5), message, is_acknowledged, created_at", "camera_id, severity, is_acknowledged"],
    ]
    
    style_tabla = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5f9e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f0f0')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ])
    
    tabla_obj = Table(tabla_schema, colWidths=[1.2*inch, 3*inch, 1.5*inch])
    tabla_obj.setStyle(style_tabla)
    contenido.append(tabla_obj)
    
    contenido.append(Spacer(1, 0.15*inch))
    
    contenido.append(Paragraph(
        "Relaciones: users 1→ alerts, cameras 1→ persons/vehicles/detections/alerts, detections 1→ alerts",
        style_texto
    ))
    
    contenido.append(PageBreak())
    
    # ============== 6. ENDPOINTS API ==============
    contenido.append(Paragraph("6. Endpoints API REST", style_titulo_seccion))
    
    contenido.append(Paragraph("Autenticación", style_titulo_subseccion))
    
    endpoints_auth = """
    POST /api/auth/login - Validación de credenciales, retorna JWT token<br/>
    POST /api/auth/logout - Destruye sesión<br/>
    POST /api/auth/register - Registra nuevo usuario admin<br/>
    GET /api/auth/me - Datos del usuario autenticado
    """
    
    contenido.append(Paragraph(endpoints_auth, style_texto))
    
    contenido.append(Spacer(1, 0.1*inch))
    contenido.append(Paragraph("Cámaras", style_titulo_subseccion))
    
    endpoints_cam = """
    GET /api/camaras - Lista todas las cámaras<br/>
    GET /api/camaras/{camera_id} - Detalles de cámara específica<br/>
    POST /api/camaras - Registra nueva cámara<br/>
    PUT /api/camaras/{camera_id} - Actualiza configuración<br/>
    DELETE /api/camaras/{camera_id} - Elimina cámara
    """
    
    contenido.append(Paragraph(endpoints_cam, style_texto))
    
    contenido.append(Spacer(1, 0.1*inch))
    contenido.append(Paragraph("Detecciones", style_titulo_subseccion))
    
    endpoints_det = """
    POST /api/deteccion/imagen - Detección en imagen estática<br/>
    POST /api/deteccion/video - Detección en archivo de video<br/>
    GET /api/deteccion/stats - Estadísticas de detecciones
    """
    
    contenido.append(Paragraph(endpoints_det, style_texto))
    
    contenido.append(Spacer(1, 0.1*inch))
    contenido.append(Paragraph("Video, Análisis y Reportes", style_titulo_subseccion))
    
    endpoints_otros = """
    GET /api/video/stream/{camera_id} - WebSocket stream en tiempo real<br/>
    GET /api/video/snapshot/{camera_id} - Captura instantánea<br/>
    GET /api/personas - Lista de personas detectadas<br/>
    GET /api/vehiculos - Lista de vehículos detectados<br/>
    GET /api/alertas - Lista de alertas por cámara<br/>
    GET /api/reportes/pdf - Genera reporte PDF<br/>
    GET /api/reportes/estadisticas - Estadísticas en JSON<br/>
    GET /api/analisis/dashboard - Datos completos del dashboard<br/>
    GET /api/analisis/tendencias - Tendencias por período
    """
    
    contenido.append(Paragraph(endpoints_otros, style_texto))
    
    contenido.append(PageBreak())
    
    # ============== 7. SERVICIOS ==============
    contenido.append(Paragraph("7. Servicios Implementados", style_titulo_seccion))
    
    servicios_desc = """
    <b>DetectionService</b> - Interfaz con modelo YOLOv8, soporte CPU/GPU automático, PyTorch 2.6 compatible.<br/>
    <br/>
    <b>DetectionPipeline</b> - Pipeline completo (captura → detección → almacenamiento), procesamiento asincrónico.<br/>
    <br/>
    <b>ReportService</b> - Generación de reportes PDF con tablas, gráficos y análisis.<br/>
    <br/>
    <b>CacheService</b> - Gestión de caché con Redis, sesiones, rate limiting.<br/>
    <br/>
    <b>AuthService</b> - Autenticación JWT, Bcrypt 12 rounds, cookies seguras.<br/>
    <br/>
    <b>VideoProcessor</b> - Renderizado de detecciones, compresión de frames (MJPEG, H264, H265).<br/>
    <br/>
    <b>FaceRecognitionService</b> - Reconocimiento facial con DeepFace (VGGFace2, FaceNet).<br/>
    <br/>
    <b>BehaviorPredictorService</b> - Predicción de comportamiento anómalo (loitering, crowd, congestion).
    """
    
    contenido.append(Paragraph(servicios_desc, style_texto))
    
    contenido.append(PageBreak())
    
    # ============== 8. SEGURIDAD ==============
    contenido.append(Paragraph("8. Seguridad y Autenticación", style_titulo_seccion))
    
    seg_auth = """
    <b>Autenticación</b><br/>
    JWT (JSON Web Tokens) + Session Cookies<br/>
    Algoritmo: HS256 (HMAC + SHA256)<br/>
    Expiración: 24 horas configurable<br/>
    <br/>
    <b>Hashing de Contraseñas</b><br/>
    Algoritmo Bcrypt con 12 rounds de salt<br/>
    Verificación time-safe contra timing attacks<br/>
    <br/>
    <b>Rate Limiting</b><br/>
    SlowAPI por IP remota<br/>
    Login: 5 intentos/15 minutos<br/>
    API general: 100 requests/minuto<br/>
    Detección: 50 requests/minuto<br/>
    <br/>
    <b>CORS</b><br/>
    Desarrollo: todas las origins<br/>
    Producción: dominios específicos<br/>
    <br/>
    <b>Validación de Entrada</b><br/>
    Pydantic Models con type hints<br/>
    Restricciones: min_length, max_length, regex<br/>
    File uploads: tamaño máximo, extensiones permitidas<br/>
    <br/>
    <b>Encriptación en Tránsito</b><br/>
    HTTPS/SSL con TLS<br/>
    Certificados auto-firmados (desarrollo)<br/>
    Certificados válidos (producción - Let's Encrypt)<br/>
    <br/>
    <b>Protección contra Ataques</b><br/>
    SQL Injection: SQLAlchemy ORM (queries parametrizadas)<br/>
    XSS: Sanitización frontend + Content-Security-Policy<br/>
    CSRF: SameSite cookies
    """
    
    contenido.append(Paragraph(seg_auth, style_texto))
    
    contenido.append(PageBreak())
    
    # ============== 9. INSTALACION ==============
    contenido.append(Paragraph("9. Instalación y Configuración", style_titulo_seccion))
    
    contenido.append(Paragraph("Requisitos Mínimos", style_titulo_subseccion))
    
    req_min = """
    Python 3.9+ (probado en 3.9, 3.10, 3.11)<br/>
    pip (gestor de paquetes)<br/>
    virtualenv o conda<br/>
    MySQL 8.0+ (producción) / SQLite 3 (desarrollo)<br/>
    Git (opcional)<br/>
    Docker (opcional)
    """
    
    contenido.append(Paragraph(req_min, style_texto))
    
    contenido.append(Spacer(1, 0.15*inch))
    contenido.append(Paragraph("Pasos de Instalación", style_titulo_subseccion))
    
    pasos_inst = """
    <b>1.</b> Descargar/clonar proyecto<br/>
    <b>2.</b> Crear virtual environment: python -m venv venv<br/>
    <b>3.</b> Activar: venv\Scripts\activate (Windows) o source venv/bin/activate (Linux)<br/>
    <b>4.</b> Instalar dependencias: pip install -r backend/requirements.txt<br/>
    <b>5.</b> Descargar modelo YOLO: python -c "from ultralytics import YOLO; YOLO('yolov8x.pt')"<br/>
    <b>6.</b> Configurar base de datos (crear .env)<br/>
    <b>7.</b> Inicializar BD: python backend/init_db.py<br/>
    <b>8.</b> Crear admin: python backend/setup_admin.py<br/>
    <b>9.</b> Ejecutar: python backend/app.py<br/>
    <b>10.</b> Acceder: http://localhost:8000
    """
    
    contenido.append(Paragraph(pasos_inst, style_texto))
    
    contenido.append(Spacer(1, 0.15*inch))
    
    contenido.append(Paragraph("Variables de Entorno (.env)", style_titulo_subseccion))
    
    env_vars = """
    DATABASE_TYPE=sqlite<br/>
    JWT_SECRET_KEY=super_secret_key_cambiar_produccion<br/>
    JWT_ALGORITHM=HS256<br/>
    JWT_EXPIRATION_HOURS=24<br/>
    SESSION_SECRET_KEY=session_secret_cambiar_produccion<br/>
    DEBUG=True                    (False en producción)
    """
    
    contenido.append(Paragraph(env_vars, style_texto))
    
    contenido.append(PageBreak())
    
    # ============== 10. DEPLOYMENT ==============
    contenido.append(Paragraph("10. Deployment", style_titulo_seccion))
    
    contenido.append(Paragraph("Docker - Desarrollo", style_titulo_subseccion))
    
    docker_dev = """
    Requisitos: Docker v24+, Docker Compose v2+<br/>
    <br/>
    Comandos:<br/>
    docker-compose build<br/>
    docker-compose up -d<br/>
    docker-compose ps<br/>
    docker-compose logs -f backend
    """
    
    contenido.append(Paragraph(docker_dev, style_texto))
    
    contenido.append(Spacer(1, 0.1*inch))
    
    contenido.append(Paragraph("Deployment Manual (VPS/Cloud)", style_titulo_subseccion))
    
    deploy_manual = """
    Distribuciones soportadas: Ubuntu 20.04+, Debian 11+<br/>
    <br/>
    Pasos:<br/>
    1. Actualizar sistema: sudo apt update && apt upgrade<br/>
    2. Instalar dependencias: sudo apt install python3.11 git mysql-server<br/>
    3. Clonar repositorio y crear venv<br/>
    4. Instalar dependencias Python<br/>
    5. Configurar .env con valores de producción<br/>
    6. Crear servicio systemd<br/>
    7. Configurar Nginx como reverse proxy<br/>
    8. Configurar SSL con Let's Encrypt (certbot)<br/>
    9. Iniciar servicio: sudo systemctl start vigilancia
    """
    
    contenido.append(Paragraph(deploy_manual, style_texto))
    
    contenido.append(Spacer(1, 0.1*inch))
    
    contenido.append(Paragraph("Configuración Producción", style_titulo_subseccion))
    
    config_prod = """
    DEBUG=False<br/>
    Actualizar JWT_SECRET_KEY y SESSION_SECRET_KEY<br/>
    Usar MySQL server dedicado<br/>
    Backups automáticos de BD<br/>
    Monitoreo: Prometheus + Grafana<br/>
    Logs centralizados: ELK Stack<br/>
    Rate limiting ajustado por load
    """
    
    contenido.append(Paragraph(config_prod, style_texto))
    
    contenido.append(PageBreak())
    
    # ============== 11. CARACTERISTICAS ==============
    contenido.append(Paragraph("11. Características Implementadas", style_titulo_seccion))
    
    contenido.append(Paragraph("Core", style_titulo_subseccion))
    
    features_core = """
     Detección de objetos en tiempo real (YOLOv8)<br/>
     Clasificación automática (personas, vehículos)<br/>
     Dashboard de monitoreo web<br/>
     Base de datos relacional (MySQL/SQLite)<br/>
     Autenticación JWT + Sessions<br/>
     API REST documentada (OpenAPI/Swagger)<br/>
     Rate limiting por IP<br/>
     CORS configurado
    """
    
    contenido.append(Paragraph(features_core, style_texto))
    
    contenido.append(Spacer(1, 0.1*inch))
    contenido.append(Paragraph("Captura de Video", style_titulo_subseccion))
    
    features_video = """
     Cámaras locales (webcam)<br/>
     Cámaras IP (RTSP)<br/>
     Archivos de video (MP4, AVI, MOV)<br/>
     Streaming UDP desde clientes remotos<br/>
     Múltiples cámaras simultáneamente<br/>
     Configuración de resolución y FPS<br/>
     Configuración de codec (H264, H265, MJPEG)
    """
    
    contenido.append(Paragraph(features_video, style_texto))
    
    contenido.append(Spacer(1, 0.1*inch))
    contenido.append(Paragraph("Análisis e Inteligencia", style_titulo_subseccion))
    
    features_ia = """
     Reconocimiento facial (DeepFace)<br/>
     Predicción de comportamiento anómalo<br/>
     Estadísticas en tiempo real<br/>
     Horas pico de detección<br/>
     Tendencias temporales<br/>
     Análisis por cámara<br/>
     Caché Redis para lecturas rápidas
    """
    
    contenido.append(Paragraph(features_ia, style_texto))
    
    contenido.append(Spacer(1, 0.1*inch))
    contenido.append(Paragraph("Frontend", style_titulo_subseccion))
    
    features_front = """
     Login seguro con JWT<br/>
     Dashboard responsive<br/>
     Stream en vivo (MJPEG)<br/>
     Widgets de estadísticas<br/>
     Tablas de historial<br/>
     Filtros por fecha/cámara<br/>
     Descarga de reportes PDF<br/>
     Panel de alertas<br/>
     Gestor de cámaras<br/>
     Mobile-friendly
    """
    
    contenido.append(Paragraph(features_front, style_texto))
    
    contenido.append(PageBreak())
    
    # ============== 12. REQUISITOS SISTEMA ==============
    contenido.append(Paragraph("12. Requisitos del Sistema", style_titulo_seccion))
    
    tabla_requisitos = [
        ["Escenario", "CPU", "RAM", "Disco", "GPU"],
        ["Desarrollo", "Dual-core 2.0 GHz", "4GB", "10GB", "Opcional"],
        ["Producción 1-4 cam", "Quad-core 2.5 GHz", "8GB", "50GB SSD", "Recomendado"],
        ["Producción 5-10 cam", "8 cores 2.5+ GHz", "16GB", "100GB SSD", "NVIDIA 8GB+"],
        ["Producción 10+ cam", "16+ cores 3.0+ GHz", "32GB+", "500GB SSD RAID", "GPU Cluster"],
    ]
    
    tabla_req = Table(tabla_requisitos, colWidths=[1.4*inch, 1.3*inch, 1.2*inch, 1.3*inch, 1.5*inch])
    tabla_req.setStyle(style_tabla)
    contenido.append(tabla_req)
    
    contenido.append(Spacer(1, 0.2*inch))
    
    navegadores = """
    <b>Navegadores Soportados</b><br/>
     Chrome/Chromium 90+<br/>
     Firefox 88+<br/>
     Safari 14+<br/>
     Edge 90+<br/>
     Internet Explorer (no soportado)
    """
    
    contenido.append(Paragraph(navegadores, style_texto))
    
    contenido.append(Spacer(1, 0.15*inch))
    
    dependencias = """
    <b>Dependencias Externas Requeridas</b><br/>
    Python 3.9+<br/>
    MySQL 8.0+ o SQLite 3<br/>
    Redis 6.0+ (para sesiones)<br/>
    <br/>
    <b>Dependencias Opcionales</b><br/>
    GPU NVIDIA + CUDA 11.8+<br/>
    Docker (containerización)<br/>
    Nginx (reverse proxy)<br/>
    Let's Encrypt (SSL)
    """
    
    contenido.append(Paragraph(dependencias, style_texto))
    
    contenido.append(PageBreak())
    
    # ============== CIERRE ==============
    contenido.append(Spacer(1, 1*inch))
    
    cierre = """
    <b>Fin de Documentación Técnica</b><br/>
    <br/>
    Versión 1.0.0<br/>
    Abril 2026<br/>
    Proyecto Final ASIR<br/>
    Sistema de Vigilancia Inteligente
    """
    
    contenido.append(Paragraph(
        cierre,
        ParagraphStyle('Cierre', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER, textColor=colors.HexColor('#2e5f9e'))
    ))
    
    # Generar PDF
    doc.build(contenido)
    
    print(f" PDF generado exitosamente: {filename}")
    print(f"  Ubicación: {os.path.abspath(filename)}")
    print(f"  Tamaño: {os.path.getsize(filename) / 1024:.2f} KB")

if __name__ == "__main__":
    generar_pdf_tecnico()
