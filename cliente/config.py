"""
Configuration para Cliente de Cámara
"""

# ═══════════════════════════════════════════════════════════════════
# SERVIDOR (Central)
# ═══════════════════════════════════════════════════════════════════

SERVER_HOST = "192.168.1.100"  # IP del servidor central
SERVER_PORT = 5005              # Puerto UDP

# ═══════════════════════════════════════════════════════════════════
# CÁMARA (Cliente)
# ═══════════════════════════════════════════════════════════════════

# Fuente de video
# Opciones:
#   0 = Webcam local
#   "rtsp://..." = Cámara IP (Hikvision, Dahua, etc)
#   "video.mp4" = Archivo de video
CAMERA_SOURCE = 0

# ID de la cámara (para identificar en servidor)
CAMERA_ID = "CAMERA_01"

# Resolución (width, height)
# Opciones: (640, 480), (1280, 720), (1920, 1080)
RESOLUTION = (640, 480)

# FPS (frames per second)
FPS = 15

# ═══════════════════════════════════════════════════════════════════
# COMPRESIÓN
# ═══════════════════════════════════════════════════════════════════

# Codec de compresión
# Opciones: 'h264', 'h265', 'mjpeg'
# h264: Mayor compatibilidad, balance bueno
# h265: Mejor compresión, menos CPU en rx
# mjpeg: Rápido pero menos compresión
VIDEO_CODEC = 'h264'

# Calidad JPEG (0-100)
# Menor = más compresión, peor calidad
JPEG_QUALITY = 70

# Máximo tamaño de paquete UDP (bytes)
# UDP típicamente tiene límite ~1500 bytes
# Frames grandes se dividirán en múltiples paquetes
MAX_PACKET_SIZE = 1400

# ═══════════════════════════════════════════════════════════════════
# RED
# ═══════════════════════════════════════════════════════════════════

# Timeout de conexión (segundos)
CONNECTION_TIMEOUT = 30

# Reintentos de conexión
MAX_RETRIES = 5

# Intervalo entre reintentos (segundos)
RETRY_INTERVAL = 5

# ═══════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════

# Nivel de logging: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL = "INFO"

# Archivo de log
LOG_FILE = "camera_client.log"

# ═══════════════════════════════════════════════════════════════════
# DIAGNÓSTICO
# ═══════════════════════════════════════════════════════════════════

# Mostrar FPS actual
SHOW_FPS = True

# Mostrar tamaño de frames
SHOW_FRAME_SIZE = True

# Guardar frames localmente (para debug)
# Desactivar en producción
SAVE_LOCAL_FRAMES = False
SAVE_FRAMES_PATH = "./frames_debug/"
