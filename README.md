# Sistema de Vigilancia Inteligente

**Proyecto Final de Grado — ASIR 2026**  
Manuel Leyes · CF GS Administración de Sistemas Informáticos en Red

Sistema completo de detección en tiempo real con inteligencia artificial: detecta personas y vehículos mediante YOLOv8, streaming de vídeo en vivo, dashboard web, alertas, reportes PDF y API REST con más de 50 endpoints.

---

## Requisitos previos

| Requisito | Versión mínima |
|-----------|----------------|
| Python | 3.10+ |
| RAM | 4 GB (8 GB recomendado con IA completa) |
| Espacio en disco | ~2 GB (dependencias + modelo YOLO) |
| Conexión a internet | Para la instalación inicial |

---

## Instalación desde cero

> El script `setup.py` hace **todo automáticamente**: crea el entorno virtual, instala las dependencias, descarga el modelo YOLOv8x (~131 MB) y arranca el servidor.

```bash
# 1. Clonar el repositorio
git clone https://github.com/manuleyes/tfg_asir.git
cd tfg_asir

# 2. Ejecutar el instalador (una sola vez)
python setup.py
```

El navegador se abrirá automáticamente al finalizar.

---

## Arranque rápido (tras la primera instalación)

```bash
# Windows
.\.venv\Scripts\Activate.ps1
python autorun\startup_new.py

# Linux / macOS
source .venv/bin/activate
python autorun/startup_new.py
```

---

## URLs de acceso

| Recurso | URL |
|---------|-----|
| **Login** | http://127.0.0.1:16000/ |
| **Dashboard** | http://127.0.0.1:16000/dashboard |
| **Detección en vivo** | http://127.0.0.1:16000/live-detection |
| **API Docs (Swagger)** | http://127.0.0.1:16000/api/docs |

**Credenciales por defecto:** `admin` / `admin123` *(cámbialas tras el primer acceso)*

---

## Estructura del proyecto

```
setup.py                   ← Instalador automático (punto de entrada)
backend/
  app.py                   ← Servidor FastAPI principal
  config.py                ← Configuración centralizada (.env)
  models/                  ← Modelos SQLAlchemy (BD)
  routes/                  ← Endpoints de la API REST
  services/                ← Lógica de IA y detección
  auth/                    ← JWT y gestión de sesiones
frontend/
  html/                    ← Páginas web
  js/                      ← Lógica cliente
  css/                     ← Estilos
autorun/
  startup_new.py           ← Arranque rápido del servidor
  tunnel.py                ← Túnel SSH para acceso remoto
cliente/
  camera_streaming_client.py ← Cliente para cámaras remotas
```

> El modelo `yolov8x.pt` **no se incluye en el repositorio**. Se descarga automáticamente al ejecutar `setup.py`.

---

## Acceso remoto (túnel SSH)

Para exponer el sistema en internet sin configurar el router:

```bash
python autorun/tunnel.py
```

Genera una URL pública HTTPS tipo `https://xxxx.lhr.life` sin instalar nada extra (usa el SSH nativo del sistema).

---

## Variables de entorno

Copia `.env.example` a `.env` y ajusta los valores:

```bash
cp .env.example .env
```

| Variable | Descripción | Por defecto |
|----------|-------------|-------------|
| `DATABASE_TYPE` | `sqlite` o `mysql` | `sqlite` |
| `JWT_SECRET_KEY` | Clave secreta JWT | *(cambiar)* |
| `SMTP_USER` | Email para alertas | *(opcional)* |
| `PUBLIC_IP` | IP pública del servidor | `localhost` |

---

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | FastAPI + Uvicorn |
| IA / Detección | YOLOv8x (Ultralytics) |
| Reconocimiento facial | DeepFace |
| Predicción comportamiento | LSTM (TensorFlow) |
| Base de datos | SQLite / MySQL (SQLAlchemy) |
| Caché | Redis |
| Frontend | HTML5 + JS vanilla |
| Autenticación | JWT + sesiones |
| Reportes | ReportLab (PDF) |

---

## Estructura del Proyecto

```
.
├── backend/              #  Servidor FastAPI (50+ endpoints)
├── frontend/             #  Páginas HTML/CSS/JS
├── pruebas/              #  Tests automatizados
├── docs_proyecto/        #  Documentación completa
├── configuracion/        #  .env, certificados SSL
├── modelos/              #  Modelos YOLO (IA)
├── utilidades/           #  Scripts helpers
└── run_project.py        #  Script principal
```

**Ver estructura completa:** [`docs_proyecto/ESTRUCTURA_PROYECTO.md`](docs_proyecto/ESTRUCTURA_PROYECTO.md)

---

## Documentación

- **[Inicio Rápido](docs_proyecto/INICIO_RAPIDO.md)**  - Comenzar en 5 minutos
- **[Estructura del Proyecto](docs_proyecto/ESTRUCTURA_PROYECTO.md)** - Organización detallada
- **[Guía Técnica](docs_proyecto/TECHNICAL_GUIDE.md)** - Detalles de implementación
- **[Manual de Usuario](docs_proyecto/USER_MANUAL.md)** - Cómo usar el sistema
- **[Guía de Despliegue](docs_proyecto/DEPLOYMENT_GUIDE.md)** - Producción

---

## Credenciales Predeterminadas

| Campo | Valor |
|-------|-------|
| Usuario | `admin` |
| Contraseña | `admin123` |

*Cambiar en `utilidades/init_db.py`*

---

## ️ Comandos Disponibles

### Ejecutar Servidor
```bash
python run_project.py
```

### Ejecutar Tests
```bash
cd pruebas && python run_tests.py
```

### Inicializar Base de Datos
```bash
python utilidades/init_db.py
```

### Descargar Modelos YOLO
```bash
python utilidades/download_yolo.py
```

### Instalar Dependencias
```bash
pip install -r backend/requirements.txt
```

---

## Características Principales

### Backend (FastAPI)
-  50+ endpoints REST
-  Autenticación JWT
-  Validación Pydantic
-  Rate limiting
-  CORS configurado

### Detección IA (YOLO)
-  YOLOv8-XLarge (80 clases COCO)
-  YOLOv10-Medium (rápido)
-  Detección en tiempo real
-  Overlay en video

### Base de Datos (SQLite)
-  5 tablas normalizadas
-  Modelos SQLAlchemy ORM
-  Relaciones foreign key
-  Índices de performance

### Frontend (HTML/CSS/JS)
-  Dashboard responsive
-  7 páginas funcionales
-  Validación de formularios
-  Tablas dinámicas

### Reportes
-  PDF generation (ReportLab)
-  JSON export
-  Estadísticas
-  Gráficos

---

## API REST - Módulos Principales

| Módulo | Propósito | Rutas |
|--------|-----------|-------|
| **auth** | Autenticación | `/api/auth/*` |
| **cameras** | Gestión de cámaras | `/api/camaras/*` |
| **persons** | Personas detectadas | `/api/personas/*` |
| **vehicles** | Vehículos detectados | `/api/vehiculos/*` |
| **alerts** | Sistema de alertas | `/api/alertas/*` |
| **detection** | Detección YOLO | `/api/deteccion/*` |
| **video** | Streaming MJPEG | `/api/video/*` |
| **analysis** | Análisis estadísticos | `/api/analisis/*` |
| **reports** | Generación de reportes | `/api/reportes/*` |

**Ver todos en:** `http://127.0.0.1:16000/api/docs`

---

## ️ Configuración

### Puerto (16000)
Configurable en `backend/app.py`:
```python
port=16000  # Línea ~200
```

### Base de Datos
Especificada en `configuracion/.env`:
```env
DATABASE_URL=sqlite:///./vigilancia.db
```

### Modelos YOLO
En `modelos/`:
- `yolov8x.pt` (136MB) - Más preciso
- `yolov10m.pt` (33MB) - Más rápido

---

##  ¿Necesitas Ayuda?

### Ver API disponible
```
http://127.0.0.1:16000/api/docs
```

### Leer documentación
Consulta la carpeta `docs_proyecto/`

### Ejecutar tests
```bash
cd pruebas && python run_tests.py
```

---

## Stack Tecnológico

| Componente | Tecnología |
|-----------|-----------|
| **Backend** | FastAPI 0.104+ |
| **BD** | SQLite 3.x |
| **IA** | YOLOv8 + PyTorch 2.6 |
| **Video** | OpenCV 4.8+ |
| **Reportes** | ReportLab |
| **Frontend** | HTML5/CSS3/JS Vanilla |
| **Testing** | Pytest |
| **Seguridad** | JWT + Bcrypt |

---

## Roadmap

-  Estructura organizada
-  Puerto 16000 configurado
-  Documentación completa
-  En desarrollo: Mejoras UI/UX
-  Planeado: Dashboard mejorado

---

## Soporte

Para problemas específicos, consulta:
- **Estructura:** [`ESTRUCTURA_PROYECTO.md`](docs_proyecto/ESTRUCTURA_PROYECTO.md)
- **Técnica:** [`TECHNICAL_GUIDE.md`](docs_proyecto/TECHNICAL_GUIDE.md)
- **Usuario:** [`USER_MANUAL.md`](docs_proyecto/USER_MANUAL.md)

---

**Estado:**  Listo para Producción  
**Última actualización:** 16/04/2026  
**Puerto:** 16000 (DNAT configurado)

 **¡Disfruta el proyecto!**
# Sistema de Vigilancia Inteligente - Proyecto Final ASIR

## Descripción General

Sistema de monitoreo y vigilancia inteligente que detecta personas y vehículos en tiempo real usando visión por computadora (YOLO), con gestión de datos en base de datos MySQL y un dashboard web seguro.

### Características principales:

 **Detección en tiempo real** - Personas y vehículos con IA  
 **Dashboard web** - Monitoreo desde navegador  
 **Base de datos MySQL** - Histórico de detecciones  
 **Gestión de BD desde web** - Consultas y administración  
 **Autenticación JWT** - Login admin con seguridad  
 **API REST** - Backend robusto con FastAPI  
 **Frontend vanilla** - HTML, CSS, JavaScript sin frameworks  

---

## Objetivo del Proyecto

Desarrollar un sistema de vigilancia que:

1. **Capture video** en tiempo real de cámaras locales o remotas
2. **Detecte personas y vehículos** usando modelos de IA pre-entrenados
3. **Almacene información** de detecciones en MySQL (ID, descripción, rasgos, etc)
4. **Presente un dashboard** seguro para monitoreo y análisis
5. **Permite gestión de BD** desde interfaz web (queries, campos, etc)
6. **Genere alertas y reportes** automáticos

---

## Stack Tecnológico

| Componente | Tecnología |
|-----------|-----------|
| **Backend** | FastAPI (Python 3.9+) |
| **Base de Datos** | MySQL 8.0+ |
| **Frontend** | HTML5, CSS3, JavaScript Vanilla |
| **Autenticación** | JWT + Bcrypt |
| **Visión por IA** | YOLOv8 + OpenCV |
| **Virtualización** | Docker + docker-compose |
| **Seguridad** | CORS, Rate Limiting, HTTPS (opcional) |

---

## Estructura del Proyecto

```
c:\Users\usuario\Desktop\Proyecto final\
├── backend/                    # Código Python FastAPI
│   ├── auth/                   # Autenticación JWT
│   ├── models/                 # Modelos SQLAlchemy
│   ├── routes/                 # Endpoints API
│   ├── middleware/             # Validaciones, CORS, etc
│   ├── services/               # Lógica de negocio
│   ├── app.py                  # Aplicación principal
│   ├── config.py               # Configuración
│   └── requirements.txt        # Dependencias
│
├── frontend/                   # Código HTML/CSS/JS
│   ├── css/                    # Hojas de estilo
│   ├── js/                     # Scripts JavaScript
│   ├── pages/                  # Páginas HTML específicas
│   └── index.html              # Página principal (Login)
│
├── docker/                     # Ficheros Docker
│   ├── Dockerfile              # Imagen FastAPI
│   └── docker-compose.yml      # Orquestación contenedores
│
├── docs/                       # Documentación
│   ├── ARQUITECTURA.md         # Detalles arquitectura
│   ├── PLAN.md                 # Plan de desarrollo
│   ├── SEGURIDAD.md            # Especificaciones seguridad
│   ├── API.md                  # Documentación endpoints
│   └── SETUP.md                # Instrucciones instalación
│
└── README.md                   # Este archivo
```

---

##  Quick Start (después de implementación)

```bash
# 1. Clonar/descargar proyecto
cd "c:\Users\usuario\Desktop\Proyecto final"

# 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate

# 3. Instalar dependencias
pip install -r backend/requirements.txt

# 4. Configurar MySQL
mysql -u root -p
CREATE DATABASE vigilancia_db;

# 5. Ejecutar FastAPI
python backend/app.py

# 6. Abrir navegador
http://localhost:16000
```

---

## URLs Principales

### Login y Acceso
- `http://localhost:16000/` - **Login** (sin autenticación)
- `http://localhost:16000/dashboard` - **Dashboard** (requiere JWT)

### Gestión
- `http://localhost:16000/camaras` - Gestión de cámaras
- `http://localhost:16000/bd` - Gestor de BD (queries)
- `http://localhost:16000/perfil` - Configuración de admin

### Histórico y análisis
- `http://localhost:16000/personas` - Personas detectadas
- `http://localhost:16000/vehiculos` - Vehículos detectados
- `http://localhost:16000/alertas` - Alertas del sistema
- `http://localhost:16000/reportes` - Generar reportes

### API REST (Backend)
- `POST /api/auth/login` - Obtener JWT
- `GET /api/camaras` - Listar cámaras
- `GET /api/personas` - Histórico personas (JSON)
- `GET /api/vehiculos` - Histórico vehículos (JSON)
- `POST /api/bd/query` - Ejecutar queries (admin)

---

## Seguridad Implementada

 **Autenticación JWT** - Token de 24h para sesiones  
 **Hash de contraseñas** - Bcrypt para almacenamiento seguro  
 **CORS** - Restricción de origen  
 **Rate Limiting** - Protección contra brute-force  
 **Validación de inputs** - Prevención de inyecciones  
 **Middleware** - Validación de permisos en todas las rutas protegidas  

---

## Plan de Desarrollo

**Tiempo estimado:** Menos de 1 mes (4 semanas)

| Fase | Tareas | Duración |
|------|--------|----------|
| **Semana 1** | Arquitectura, FastAPI setup, MySQL, JWT login | 7 días |
| **Semana 2** | YOLO integration, capturas de cámara, almacenamiento | 7 días |
| **Semana 3** | Dashboard web, histórico, búsqueda y filtros | 7 días |
| **Semana 4** | Alertas, reportes, testing, documentación final | 7 días |

---

## Requisitos Previos

- Python 3.9+
- MySQL 8.0+
- Git (opcional)
- Navegador moderno (Chrome, Firefox, Edge)
- Cámara web o fuente de video local

---

## Documentación Disponible

- [ARQUITECTURA.md](docs/ARQUITECTURA.md) - Desglose técnico
- [PLAN.md](docs/PLAN.md) - Timeline detallado
- [SEGURIDAD.md](docs/SEGURIDAD.md) - Implementación de seguridad
- [API.md](docs/API.md) - Endpoints y payloads
- [SETUP.md](docs/SETUP.md) - Instalación paso a paso

---

## Autor

**Proyecto Final ASIR** - Sistema de vigilancia inteligente  
Curso: Grado Superior de Administración de Sistemas Informáticos en Red

---

## Notas

Este proyecto es educativo y está diseñado para cumplir con los requisitos del grado ASIR. 
Para producción, se recomienda implementar HTTPS, bases de datos redundantes y auditoría.

---

**Última actualización:** Abril 2026  
**Estado:** 🟡 En Planificación

---

## 📹 Cliente de Cámara (UDP Streaming)

Módulo Python para transmitir video desde cámaras (IP, móviles, webcams) al servidor central por UDP con compresión en tiempo real.

### Características
- **Streaming UDP** — Baja latencia, 99% menos ancho de banda que video crudo
- **Multi-cámara** — Múltiples clientes simultáneos
- **Compresión automática** — JPEG adaptativo
- **Reconexión automática** — Recuperación ante fallos de red

### Requisitos
```bash
Python 3.8+  |  OpenCV 4.8+  |  NumPy 1.24+
```

### Instalación
```bash
cd cliente
pip install -r requirements.txt
```

### Configuración (`cliente/config.py`)
```python
SERVER_HOST = "192.168.1.100"  # IP del servidor
SERVER_PORT = 5005              # Puerto UDP
CAMERA_SOURCE = 0               # 0=webcam, "rtsp://..." = IP cam
CAMERA_ID = "CAMERA_01"         # Identificador único
RESOLUTION = (640, 480)
FPS = 15
JPEG_QUALITY = 70               # 0-100
```

### Uso básico
```python
from cliente import CameraClient

client = CameraClient(camera_id="CAM_01", camera_source=0, server_host="127.0.0.1")
client.start()

import time
while True:
    time.sleep(10)
    client.print_stats()
```

### Fuentes de vídeo soportadas
```python
# Webcam local
config.CAMERA_SOURCE = 0

# Cámara IP (Hikvision, Dahua, etc.)
config.CAMERA_SOURCE = "rtsp://admin:password@192.168.1.50:554/stream1"

# Archivo de vídeo
config.CAMERA_SOURCE = "grabacion.mp4"
```

### Rendimiento
| Métrica | Valor |
|---------|-------|
| Latencia UDP | 20–50 ms |
| Reducción ancho de banda | ~99 % |
| CPU por stream | ~6 % (Intel 2.4 GHz) |
| Streams por núcleo | 15+ |

### Escalabilidad
- **10 cámaras**: 1 servidor estándar, 2 CPUs, 8 GB RAM
- **100 cámaras**: Kubernetes + GPU + Redis
- **1000+**: Edge processing + Apache Spark

---

## 🧪 Tests

Suite de pruebas con pytest que cubre las tres fases del sistema de detección IA.

### Archivos de test

| Archivo | Fase | Descripción |
|---------|------|-------------|
| `tests/test_yolo_detection.py` | FASE 1 | Detección YOLO con TensorRT |
| `tests/test_behavior_prediction.py` | FASE 2 | Predicción LSTM de comportamiento |
| `tests/test_face_recognition.py` | FASE 3 | Reconocimiento facial y re-ID |
| `tests/test_detection_pipeline.py` | Integración | Pipeline completo E2E |
| `tests/test_api_endpoints.py` | API | Endpoints FastAPI |

### Ejecución
```bash
# Todos los tests
pytest tests/ -v

# Test específico
pytest tests/test_yolo_detection.py -v

# Con cobertura
pip install pytest-cov
pytest tests/ --cov=backend --cov-report=html
```

### Configuración (`configuracion/pytest.ini`)
```ini
[pytest]
testpaths = tests
python_files = test_*.py
addopts = -v --tb=short
```

### Estado de los tests

| Métrica | Objetivo | Estado |
|---------|----------|--------|
| Cobertura total | >70 % | ✅ |
| FASE 1 (YOLO) | 100 % | ✅ |
| FASE 2 (LSTM) | 80 % | ⚠️ |
| FASE 3 (Face) | 60 % | ⚠️ |
| API endpoints | 95 % | ✅ |

> ⚠️ TensorFlow y DeepFace requieren Python 3.12. Con Python 3.14 algunos tests se omiten automáticamente.
