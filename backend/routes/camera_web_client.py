"""
Endpoint para recibir camera streaming por HTTP
Mejor que UDP para WiFi/NAT
"""

import base64
import io
import os
import numpy as np
import cv2
from fastapi import APIRouter, File, UploadFile, HTTPException, Request
from services.email_service import EmailService as _EmailService
_email_svc = _EmailService()
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
import logging
from services.detection_overlay import get_overlay_processor
from config import get_settings
import requests
import time
import asyncio
import socket
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
try:
    import zoneinfo as _zoneinfo
    _TZ_MADRID = _zoneinfo.ZoneInfo('Europe/Madrid')
except Exception:
    _TZ_MADRID = None
from models.database import get_db
from models.person import Person
from models.vehicle import Vehicle
from models.camera import Camera
from models.item import DetectedItem
from services.summary_builder import get_session_summary

# Directorio base para guardar frames de sesiones (relativo a este archivo → siempre correcto)
IMAGES_BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'images'))

# Procesado cada N frames para BD+WS (1 = todos los frames)
DETECTION_FRAME_SKIP = 1

# Caché de camera_id_str → db camera id (para no hacer SELECT cada frame)
_camera_db_id_cache: dict = {}

# ── Cola de frames por cámara ─────────────────────────────────────────────────
# Executor YOLO: un solo hilo (evita paralelismo en CPU y OOM)
_YOLO_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="yolo")
# Cola asyncio por cámara: permite continuar procesando tras fin de transmisión
_frame_queues: dict = {}   # camera_id → asyncio.Queue
_worker_tasks: dict = {}   # camera_id → asyncio.Task
_background_tasks: set = set()  # Referencias fuertes para evitar GC prematuro
MAX_QUEUE_SIZE = 300        # máx frames en cola por cámara

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/v2", tags=["Camera Streaming HTTP"])

# Estadísticas globales
camera_stats = {
    'frames_received': 0,
    'bytes_received': 0,
    'active_cameras': {},
    'latest_frames': {},      # Frames YOLO anotados (worker)
    'latest_raw_frames': {},  # Frames crudos (upload) — los más recientes
    'detection_stats': {},  # Estadísticas de detecciones
    'alerts': []  # Historial de alertas
}

# Subscriptores MJPEG: camera_id -> lista de asyncio.Queue (uno por cliente conectado)
# Cada frame raw recibido se empuja inmediatamente a todas las colas activas.
_live_subs: dict = {}  # tipo: dict[str, list[asyncio.Queue]]

# Subscriptores MJPEG para frames YOLO anotados (al ritmo de la IA)
_ai_subs: dict = {}    # tipo: dict[str, list[asyncio.Queue]]

# Cache para IP pública (evitar llamadas excesivas)
_public_ip_cache = {
    'ip': None,
    'timestamp': 0,
    'cache_duration': 3600  # 1 hora
}

def get_local_ip():
    """Obtener IP local del ordenador"""
    try:
        # Crear socket para obtener la IP local real
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Conectar a un servidor DNS público (no hace envío de datos)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.warning(f"No se pudo obtener IP local: {e}")
        return "localhost"

async def get_public_ip_async():
    """Obtener IP pública desde ifconfig.me con cache"""
    current_time = time.time()
    
    # Si existe en cache y no ha expirado, retornar
    if _public_ip_cache['ip'] and (current_time - _public_ip_cache['timestamp']) < _public_ip_cache['cache_duration']:
        return _public_ip_cache['ip']
    
    try:
        # Intentar obtener IP pública desde ifconfig.me
        response = requests.get('https://ifconfig.me', timeout=5)
        if response.status_code == 200:
            ip = response.text.strip()
            _public_ip_cache['ip'] = ip
            _public_ip_cache['timestamp'] = current_time
            logger.info(f"IP pública obtenida: {ip}")
            return ip
    except requests.exceptions.RequestException as e:
        logger.warning(f"No se pudo obtener IP pública de ifconfig.me: {e}")
    except Exception as e:
        logger.warning(f"Error inesperado obteniendo IP pública: {e}")
    
    # Retornar IP configurada como fallback
    return settings.public_ip


def _stamp_timestamp(frame):
    """Estampa hora con huso horario en esquina inferior derecha del frame (in-place)."""
    try:
        ts_text = datetime.now(_TZ_MADRID).strftime('%d/%m/%Y  %H:%M:%S %Z') if _TZ_MADRID else datetime.now().strftime('%d/%m/%Y  %H:%M:%S')
    except Exception:
        ts_text = datetime.now().strftime('%d/%m/%Y  %H:%M:%S')
    h, w = frame.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = max(0.38, w / 2500)
    (tw, _), _ = cv2.getTextSize(ts_text, font, scale, 1)
    tx, ty = w - tw - 8, h - 8
    cv2.putText(frame, ts_text, (tx + 1, ty + 1), font, scale, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(frame, ts_text, (tx, ty), font, scale, (255, 255, 255), 1, cv2.LINE_AA)


async def _ensure_camera_worker(camera_id: str):
    """Crea (si no existe) la cola y el worker para esta cámara."""
    if camera_id not in _frame_queues:
        _frame_queues[camera_id] = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)
    if camera_id not in _worker_tasks or _worker_tasks[camera_id].done():
        task = asyncio.create_task(_camera_frame_worker(camera_id))
        _worker_tasks[camera_id] = task
        _background_tasks.add(task)          # referencia fuerte → evita GC
        task.add_done_callback(_background_tasks.discard)


async def _camera_frame_worker(camera_id: str):
    """
    Worker por cámara: drena la cola de frames con YOLO aunque la transmisión
    haya terminado. Se para automáticamente si lleva 60 s sin recibir nada.
    """
    queue = _frame_queues.get(camera_id)
    if queue is None:
        return
    loop = asyncio.get_event_loop()
    overlay = get_overlay_processor()
    logger.info(f"[Worker] Iniciado para cámara '{camera_id}' (cola máx {MAX_QUEUE_SIZE})")
    try:
        while True:
            try:
                frame = await asyncio.wait_for(queue.get(), timeout=60.0)
            except asyncio.TimeoutError:
                remaining = queue.qsize()
                logger.info(f"[Worker] '{camera_id}' sin frames 60 s (pendientes={remaining}) → terminando")
                break

            try:
                # YOLO en hilo dedicado — no bloquea el event loop
                frame_with_overlay, detection_info = await loop.run_in_executor(
                    _YOLO_EXECUTOR, overlay.process_frame, frame
                )

                # Estadísticas
                if camera_id not in camera_stats['detection_stats']:
                    camera_stats['detection_stats'][camera_id] = {
                        'persons_total': 0, 'cars_total': 0, 'last_detection': None
                    }
                camera_stats['detection_stats'][camera_id]['persons_total'] += detection_info.get('persons', 0)
                camera_stats['detection_stats'][camera_id]['cars_total'] += detection_info.get('cars', 0)

                boxes = detection_info.get('boxes', [])
                if detection_info.get('events'):
                    camera_stats['detection_stats'][camera_id]['last_detection'] = detection_info
                    alert = {'timestamp': datetime.now().isoformat(), 'camera_id': camera_id, 'events': detection_info['events']}
                    camera_stats['alerts'].append(alert)
                    if len(camera_stats['alerts']) > 100:
                        camera_stats['alerts'] = camera_stats['alerts'][-100:]

                # Hora en el overlay
                _stamp_timestamp(frame_with_overlay)

                # Guardar en latest_frames (dashboard en directo)
                _, jpeg = cv2.imencode('.jpg', frame_with_overlay)
                jpeg_bytes = jpeg.tobytes()
                camera_stats['latest_frames'][camera_id] = jpeg_bytes

                # Notificar subscriptores del stream IA (al ritmo del worker YOLO)
                for _aq in _ai_subs.get(camera_id, []):
                    if _aq.full():
                        try: _aq.get_nowait()
                        except Exception: pass
                    try: _aq.put_nowait(jpeg_bytes)
                    except Exception: pass

                # Guardar frame anotado en session_dir/frames/
                cam = camera_stats['active_cameras'].get(camera_id)
                if cam:
                    session_dir = cam.get('session_dir')
                    if session_dir:
                        cam['frame_count'] = cam.get('frame_count', 0) + 1
                        frames_subdir = os.path.join(session_dir, 'frames')
                        os.makedirs(frames_subdir, exist_ok=True)
                        frame_path = os.path.join(frames_subdir, f"frame_{cam['frame_count']:06d}.jpg")
                        with open(frame_path, 'wb') as fh:
                            fh.write(jpeg_bytes)

                        # Actualizar resumen: guardar mejor crop por persona/vehículo único
                        if boxes:
                            summary = get_session_summary(session_dir)
                            for box in boxes:
                                if box['type'] == 'person':
                                    summary.process_person(frame, box, box['confidence'])
                                elif box['type'] == 'car':
                                    summary.process_vehicle(frame, box, box['confidence'])

                # DB + WS
                if boxes:
                    await _save_detections_and_broadcast(camera_id, boxes, detection_info, frame.copy())

                logger.info(
                    f"[Worker] '{camera_id}' P:{detection_info.get('persons',0)} "
                    f"C:{detection_info.get('cars',0)} pendientes:{queue.qsize()}"
                )
            except Exception as e:
                logger.error(f"[Worker] Error procesando frame de '{camera_id}': {e}")
            finally:
                queue.task_done()
    except asyncio.CancelledError:
        pass
    finally:
        _frame_queues.pop(camera_id, None)
        _worker_tasks.pop(camera_id, None)
        logger.info(f"[Worker] Finalizado para '{camera_id}'")


@router.post("/camera/upload")
async def upload_camera_frame(request: Request, file: UploadFile = File(...), camera_id: str = "mobile-1"):
    """
    Recibir frame de cámara por HTTP.
    El frame se encola inmediatamente → respuesta rápida al cliente.
    El worker YOLO procesa la cola aunque la transmisión haya terminado.
    """
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image format")

        # Estadísticas globales
        camera_stats['frames_received'] += 1
        camera_stats['bytes_received'] += len(contents)

        now = time.time()
        if camera_id not in camera_stats['active_cameras']:
            session_ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            safe_id = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in camera_id)
            session_dir = os.path.join(IMAGES_BASE_DIR, f"{safe_id}_{session_ts}")
            os.makedirs(session_dir, exist_ok=True)
            logger.info(f"Nueva sesion de camara '{camera_id}' -> {session_dir}")
            client_ip = request.client.host if request.client else 'desconocida'
            # Crear subcarpetas: frames/ y resumen/ (summary_builder las crea también)
            frames_dir = os.path.join(session_dir, 'frames')
            os.makedirs(frames_dir, exist_ok=True)
            camera_stats['active_cameras'][camera_id] = {
                'frames': 0, 'last_frame_size': None, 'last_seen': now, 'first_seen': now,
                'fps': 0.0, '_fps_frames': 0, '_fps_window': now,
                'session_dir': session_dir, 'frame_count': 0,
                'client_ip': client_ip
            }
            # Inicializar el resumen de sesión (crea resumen/personas/ y resumen/vehiculos/)
            get_session_summary(session_dir)
        cam = camera_stats['active_cameras'][camera_id]
        cam['frames'] += 1
        cam['last_frame_size'] = frame.shape
        cam['last_seen'] = now
        cam['_fps_frames'] = cam.get('_fps_frames', 0) + 1
        elapsed = now - cam.get('_fps_window', now)
        if elapsed >= 3.0:
            cam['fps'] = round(cam['_fps_frames'] / elapsed, 1)
            cam['_fps_frames'] = 0
            cam['_fps_window'] = now

        # Publicar frame RAW — feed en directo (antes de YOLO)
        _preview = frame.copy()
        _stamp_timestamp(_preview)
        _, _pjpeg = cv2.imencode('.jpg', _preview, [cv2.IMWRITE_JPEG_QUALITY, 80])
        _raw_bytes = _pjpeg.tobytes()
        camera_stats['latest_raw_frames'][camera_id] = _raw_bytes

        # Notificar a todos los clientes MJPEG suscritos (event-driven, sin polling)
        for _q in _live_subs.get(camera_id, []):
            if _q.full():
                try: _q.get_nowait()  # descarta frame viejo no consumido
                except Exception: pass
            try: _q.put_nowait(_raw_bytes)
            except Exception: pass

        # Encolar frame para el worker YOLO (no bloquea el event loop)
        await _ensure_camera_worker(camera_id)
        queue = _frame_queues.get(camera_id)
        if queue is not None:
            if queue.full():
                # Cola llena: descartar el frame más antiguo para hacer hueco
                try:
                    queue.get_nowait()
                    queue.task_done()
                except Exception:
                    pass
            await queue.put(frame)

        return {
            "status": "queued",
            "camera_id": camera_id,
            "queue_pending": queue.qsize() if queue else 0,
            "frame_shape": frame.shape,
            "bytes_received": len(contents),
            "total_frames": camera_stats['frames_received']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _extract_dominant_color(frame: np.ndarray, box: dict) -> str | None:
    """
    Extrae el color dominante de un vehículo a partir del crop del bounding box.
    Devuelve un nombre de color en español o None si no se puede determinar.
    """
    try:
        x1 = int(box.get('x1', 0))
        y1 = int(box.get('y1', 0))
        x2 = int(box.get('x2', 0))
        y2 = int(box.get('y2', 0))
        h_frame, w_frame = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w_frame, x2), min(h_frame, y2)
        if x2 <= x1 + 10 or y2 <= y1 + 10:
            return None
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return None
        # Reducir para velocidad
        small = cv2.resize(crop, (48, 48))
        hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
        pixels = hsv.reshape(-1, 3).astype(np.float32)
        avg_h = float(np.mean(pixels[:, 0]))
        avg_s = float(np.mean(pixels[:, 1]))
        avg_v = float(np.mean(pixels[:, 2]))
        # Clasificar por brillo y saturación primero
        if avg_v < 45:
            return "Negro"
        if avg_v > 195 and avg_s < 35:
            return "Blanco"
        if avg_s < 40:
            return "Gris" if avg_v < 175 else "Plateado"
        # Color saturado: clasificar por matiz (H en OpenCV: 0-180)
        if avg_h < 10 or avg_h >= 170:
            return "Rojo"
        if avg_h < 25:
            return "Naranja"
        if avg_h < 38:
            return "Amarillo"
        if avg_h < 85:
            return "Verde"
        if avg_h < 130:
            return "Azul"
        return "Morado"
    except Exception:
        return None


# Ventana de deduplicación: si la misma cámara detectó una persona hace menos de N segundos,
# actualiza el registro existente en lugar de crear uno nuevo
_DEDUP_WINDOW_SECONDS = 30
# person_key → (db_id, best_confidence)  para deduplicación en memoria
_person_dedup_cache: dict = {}   # "{cam_db_id}_person" → (id, confidence, last_seen)
_vehicle_dedup_cache: dict = {}  # "{cam_db_id}_vehicle" → (id, confidence, last_seen)


def _save_detection_crop(raw_frame, box: dict, category: str, cam_id_str: str, ts_str: str):
    """Recorta la bbox del frame y guarda JPEG. Devuelve URL web relativa o None."""
    try:
        if raw_frame is None:
            return None
        x1 = max(0, int(box.get('x1', 0)))
        y1 = max(0, int(box.get('y1', 0)))
        x2 = int(box.get('x2', 0))
        y2 = int(box.get('y2', 0))
        h, w = raw_frame.shape[:2]
        x2, y2 = min(w, x2), min(h, y2)
        if x2 - x1 < 20 or y2 - y1 < 20:
            return None
        crop = raw_frame[y1:y2, x1:x2]
        save_dir = os.path.join(IMAGES_BASE_DIR, 'crops', category)
        os.makedirs(save_dir, exist_ok=True)
        safe_cam = ''.join(c if c.isalnum() or c in ('-', '_') else '_' for c in cam_id_str)
        filename = f"{safe_cam}_{ts_str}.jpg"
        filepath = os.path.join(save_dir, filename)
        cv2.imwrite(filepath, crop)
        return f"/images/crops/{category}/{filename}"
    except Exception as e:
        logger.debug(f"[Crop] Error guardando crop: {e}")
        return None


def _find_session_frame(cam_str: str, detected_at: datetime = None):
    """Devuelve URL web del frame más cercano en tiempo a detected_at, o None.
    Si detected_at es None, devuelve el primer frame de la sesión más reciente."""
    try:
        if not os.path.isdir(IMAGES_BASE_DIR):
            return None
        folders = sorted(
            (f for f in os.listdir(IMAGES_BASE_DIR) if f.startswith(cam_str + '_')),
            reverse=True  # sesión más reciente primero
        )
        for folder in folders:
            frames_dir = os.path.join(IMAGES_BASE_DIR, folder, 'frames')
            if not os.path.isdir(frames_dir):
                continue
            frames = sorted(f for f in os.listdir(frames_dir) if f.endswith('.jpg'))
            if not frames:
                continue
            if detected_at is None:
                return f"/images/{folder}/frames/{frames[0]}"
            # Obtener timestamps del primer y último frame
            first_mtime = os.path.getmtime(os.path.join(frames_dir, frames[0]))
            last_mtime  = os.path.getmtime(os.path.join(frames_dir, frames[-1]))
            first_dt = datetime.utcfromtimestamp(first_mtime)
            last_dt  = datetime.utcfromtimestamp(last_mtime)
            # Comprobar si la detección cae dentro de esta sesión
            if detected_at < first_dt or detected_at > last_dt:
                continue
            # Interpolar posición del frame
            total_secs = (last_dt - first_dt).total_seconds()
            if total_secs <= 0:
                return f"/images/{folder}/frames/{frames[0]}"
            elapsed = (detected_at - first_dt).total_seconds()
            frac = max(0.0, min(1.0, elapsed / total_secs))
            idx = int(frac * (len(frames) - 1))
            return f"/images/{folder}/frames/{frames[idx]}"
        # Fallback: primer frame de la sesión más reciente
        for folder in folders:
            frames_dir = os.path.join(IMAGES_BASE_DIR, folder, 'frames')
            if os.path.isdir(frames_dir):
                frames = sorted(f for f in os.listdir(frames_dir) if f.endswith('.jpg'))
                if frames:
                    return f"/images/{folder}/frames/{frames[0]}"
        return None
    except Exception:
        return None


async def _save_detections_and_broadcast(camera_id: str, boxes: list, detection_info: dict, raw_frame=None):
    """
    Guarda detecciones en BD y emite evento WebSocket.
    Se ejecuta como tarea async para no bloquear el upload.
    """
    try:
        from routes.websocket_routes import broadcast_detection

        db = next(get_db())
        try:
            # Obtener o crear registro de cámara en BD
            if camera_id not in _camera_db_id_cache:
                cam_record = db.query(Camera).filter(Camera.name == camera_id).first()
                if not cam_record:
                    cam_record = Camera(
                        name=camera_id,
                        url=f"mobile://{camera_id}",
                        description="Cámara móvil/portátil (auto-registrada)",
                        is_active=True,
                        location="Móvil"
                    )
                    db.add(cam_record)
                    db.commit()
                    db.refresh(cam_record)
                _camera_db_id_cache[camera_id] = cam_record.id

            db_cam_id = _camera_db_id_cache[camera_id]
            now = datetime.utcnow()
            import time as _time
            now_ts = _time.time()

            saved = []
            for box in boxes:
                det_type = box['type']
                confidence = box['confidence']

                if det_type == 'person':
                    cache_key = f"{db_cam_id}_person"
                    entry = _person_dedup_cache.get(cache_key)
                    if entry and (now_ts - entry['last_seen']) < _DEDUP_WINDOW_SECONDS:
                        db_id, best_conf = entry['db_id'], entry['confidence']
                        db.query(DetectedItem).filter(DetectedItem.id == db_id).update({
                            'times_detected': DetectedItem.times_detected + 1,
                            'detected_at': now,
                            'confidence': max(confidence, best_conf)
                        })
                        entry['last_seen'] = now_ts
                        entry['confidence'] = max(confidence, best_conf)
                    else:
                        item_id = f"{camera_id}_{now.strftime('%Y%m%d%H%M%S')}"
                        record = DetectedItem(
                            camera_id=db_cam_id,
                            item_id=item_id,
                            type='person',
                            label=item_id,
                            confidence=confidence,
                            detected_at=now,
                            created_at=now
                        )
                        db.add(record)
                        db.flush()
                        db_id = record.id
                        crop_ts = now.strftime('%Y%m%d%H%M%S%f')[:17]
                        img_url = _save_detection_crop(raw_frame, box, 'persons', camera_id, crop_ts)
                        if img_url:
                            db.query(DetectedItem).filter(DetectedItem.id == db_id).update({'image_path': img_url})
                        _person_dedup_cache[cache_key] = {
                            'db_id': db_id, 'confidence': confidence, 'last_seen': now_ts
                        }
                    saved.append(box)

                elif det_type == 'car':
                    cache_key = f"{db_cam_id}_vehicle"
                    entry = _vehicle_dedup_cache.get(cache_key)
                    if entry and (now_ts - entry['last_seen']) < _DEDUP_WINDOW_SECONDS:
                        db_id, best_conf = entry['db_id'], entry['confidence']
                        db.query(DetectedItem).filter(DetectedItem.id == db_id).update({
                            'times_detected': DetectedItem.times_detected + 1,
                            'detected_at': now,
                            'confidence': max(confidence, best_conf)
                        })
                        entry['last_seen'] = now_ts
                        entry['confidence'] = max(confidence, best_conf)
                    else:
                        color = _extract_dominant_color(raw_frame, box) if raw_frame is not None else None
                        item_id = f"vehicle_{camera_id}_{now.strftime('%Y%m%d%H%M%S')}"
                        lbl = color or 'Vehículo'
                        record = DetectedItem(
                            camera_id=db_cam_id,
                            item_id=item_id,
                            type='vehicle',
                            label=lbl,
                            confidence=confidence,
                            detected_at=now,
                            created_at=now
                        )
                        db.add(record)
                        db.flush()
                        db_id = record.id
                        crop_ts = now.strftime('%Y%m%d%H%M%S%f')[:17]
                        img_url = _save_detection_crop(raw_frame, box, 'vehicles', camera_id, crop_ts)
                        if img_url:
                            db.query(DetectedItem).filter(DetectedItem.id == db_id).update({'image_path': img_url})
                        _vehicle_dedup_cache[cache_key] = {
                            'db_id': db_id, 'confidence': confidence, 'last_seen': now_ts
                        }
                    saved.append(box)

            db.commit()

            # Emitir por WebSocket
            if saved:
                await broadcast_detection({
                    'camera_id': camera_id,
                    'persons': detection_info.get('persons', 0),
                    'cars': detection_info.get('cars', 0),
                    'boxes': saved,
                    'timestamp': now.isoformat()
                })

            # Enviar email en nuevas detecciones (solo registros nuevos, no dedup)
            _try_send_alert_email(camera_id, saved)

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error guardando detecciones en BD: {e}")


_alert_email_cooldown: dict = {}   # camera_id -> last_sent timestamp
_ALERT_EMAIL_COOLDOWN_SECONDS = 300  # máx 1 email cada 5 min por cámara

def _try_send_alert_email(camera_id: str, saved_boxes: list):
    """Envía email de alerta si hay detecciones nuevas y el servicio está configurado."""
    if not _email_svc.is_configured():
        return
    if not saved_boxes:
        return

    import time as _t
    from config import get_settings as _gs
    now_ts = _t.time()
    last = _alert_email_cooldown.get(camera_id, 0)
    if now_ts - last < _ALERT_EMAIL_COOLDOWN_SECONDS:
        return
    _alert_email_cooldown[camera_id] = now_ts

    try:
        settings = _gs()
        to_raw = getattr(settings, 'alert_email_to', settings.smtp_user)
        to_list = [x.strip() for x in to_raw.split(',') if x.strip()]
        if not to_list:
            return

        persons = sum(1 for b in saved_boxes if b['type'] == 'person')
        vehicles = sum(1 for b in saved_boxes if b['type'] == 'car')
        lines = []
        if persons:
            lines.append(f"<li><b>{persons}</b> persona(s) detectada(s)</li>")
        if vehicles:
            lines.append(f"<li><b>{vehicles}</b> veh&iacute;culo(s) detectado(s)</li>")
        if not lines:
            return

        from datetime import datetime as _dt
        ts = _dt.now().strftime('%d/%m/%Y %H:%M:%S')
        body_html = f"""
        <div style="font-family:sans-serif;max-width:500px">
          <h2 style="color:#dc2626">&#128680; Alerta de detecci&oacute;n</h2>
          <p><b>C&aacute;mara:</b> {camera_id}<br><b>Fecha/Hora:</b> {ts}</p>
          <ul>{''.join(lines)}</ul>
          <p style="color:#6b7280;font-size:12px">Sistema de Vigilancia ASIR</p>
        </div>"""
        body_text = f"Alerta [{camera_id}] {ts}: {persons} persona(s), {vehicles} vehiculo(s)"
        _email_svc.send_email(
            to=to_list,
            subject=f"[Vigilancia] Detecci\u00f3n en c\u00e1mara {camera_id}",
            body_html=body_html,
            body_text=body_text
        )
    except Exception as exc:
        logger.warning(f"Error enviando email de alerta: {exc}")


@router.get("/camera/stats")
async def get_camera_stats():
    """Obtener estadísticas de cámaras activas"""
    return {
        "total_frames": camera_stats['frames_received'],
        "total_bytes_mb": camera_stats['bytes_received'] / (1024 * 1024),
        "active_cameras": camera_stats['active_cameras'],
        "num_cameras": len(camera_stats['active_cameras']),
        "detection_stats": camera_stats['detection_stats']
    }


@router.get("/camera/active-list")
async def get_active_camera_list():
    """Lista de cámaras streaming activas con sus estadisticas"""
    now = time.time()
    result = []
    for cam_id, info in camera_stats['active_cameras'].items():
        last_seen = info.get('last_seen', 0)
        active = (now - last_seen) < 15  # activa si tuvo frame en los ultimos 15s
        det = camera_stats['detection_stats'].get(cam_id, {})
        first_seen = info.get('first_seen', 0)
        result.append({
            'camera_id': cam_id,
            'active': active,
            'frames': info.get('frames', 0),
            'fps': info.get('fps', 0.0),
            'resolution': f"{info['last_frame_size'][1]}x{info['last_frame_size'][0]}" if info.get('last_frame_size') else 'N/A',
            'first_seen': datetime.fromtimestamp(first_seen).strftime('%d/%m/%Y %H:%M:%S') if first_seen else 'N/A',
            'last_seen': datetime.fromtimestamp(last_seen).strftime('%d/%m/%Y %H:%M:%S') if last_seen else 'N/A',
            'client_ip': info.get('client_ip', '—'),
            'persons_total': det.get('persons_total', 0),
            'cars_total': det.get('cars_total', 0),
            'has_frame': cam_id in camera_stats['latest_frames'] or cam_id in camera_stats['latest_raw_frames']
        })
    return {'cameras': result, 'count': len(result)}


@router.get("/camera/alerts")
async def get_alerts(limit: int = 20):
    """Obtener historial de alertas de detección"""
    alerts = camera_stats['alerts'][-limit:]
    return {
        "total_alerts": len(camera_stats['alerts']),
        "recent_alerts": alerts
    }


@router.get("/camera/detection-summary")
async def get_detection_summary(camera_id: str = "mobile-1"):
    """Obtener resumen de detecciones para una cámara"""
    if camera_id not in camera_stats['detection_stats']:
        return {"error": "No data yet"}
    
    stats = camera_stats['detection_stats'][camera_id]
    return {
        "camera_id": camera_id,
        "persons_total": stats['persons_total'],
        "cars_total": stats['cars_total'],
        "last_detection": stats['last_detection']
    }


@router.get("/camera/latest-frame")
async def get_latest_frame(camera_id: str = "mobile-1"):
    """Obtener el último frame de una cámara (para dashboard).
    Prioriza el frame YOLO anotado; si no existe aún, devuelve el crudo."""
    annotated = camera_stats['latest_frames'].get(camera_id)
    raw       = camera_stats['latest_raw_frames'].get(camera_id)
    frame_bytes = annotated or raw
    if not frame_bytes:
        raise HTTPException(status_code=404, detail=f"Camera {camera_id} has no frames yet")
    return StreamingResponse(
        io.BytesIO(frame_bytes),
        media_type="image/jpeg"
    )


@router.get("/camera/stream/{camera_id}")
async def stream_camera_mjpeg(camera_id: str, request: Request):
    """MJPEG streaming endpoint event-driven — cada frame raw recibido se envía
    de inmediato al navegador, sin esperar al worker YOLO. Compatible con
    <img src="..."> (multipart/x-mixed-replace)."""
    BOUNDARY = b"frame"
    NO_FRAME_TIMEOUT = 60  # segundos sin frames → cerrar

    # Cola exclusiva de este cliente (maxsize=1: siempre el frame más reciente)
    q: asyncio.Queue = asyncio.Queue(maxsize=1)
    _live_subs.setdefault(camera_id, []).append(q)

    # Si ya hay un frame cacheado, enviarlo al instante (no esperar el siguiente upload)
    cached = (
        camera_stats['latest_raw_frames'].get(camera_id) or
        camera_stats['latest_frames'].get(camera_id)
    )
    if cached:
        try: q.put_nowait(cached)
        except Exception: pass

    async def mjpeg_generator():
        last_frame_time = time.time()
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    # Esperar el próximo frame (event-driven, sin busy-wait)
                    frame_bytes = await asyncio.wait_for(q.get(), timeout=2.0)
                    last_frame_time = time.time()
                    yield (
                        b"--" + BOUNDARY + b"\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" +
                        frame_bytes +
                        b"\r\n"
                    )
                except asyncio.TimeoutError:
                    if time.time() - last_frame_time > NO_FRAME_TIMEOUT:
                        break
                    # Sigue esperando (la cámara puede estar pausada)
        except asyncio.CancelledError:
            pass
        finally:
            # Limpiar subscriptor al desconectarse el cliente
            try: _live_subs.get(camera_id, []).remove(q)
            except ValueError: pass

    return StreamingResponse(
        mjpeg_generator(),
        media_type=f"multipart/x-mixed-replace; boundary={BOUNDARY.decode()}",
        headers={"Cache-Control": "no-cache, no-store", "X-Accel-Buffering": "no"},
    )


@router.get("/camera/stream-ai/{camera_id}")
async def stream_camera_ai_mjpeg(camera_id: str, request: Request):
    """MJPEG streaming de frames anotados por YOLO — al ritmo de la IA.
    Cada frame que emite es el último que el worker YOLO procesó con bounding boxes.
    Compatible con <img src="..."> (multipart/x-mixed-replace)."""
    BOUNDARY = b"frame"
    NO_FRAME_TIMEOUT = 60  # segundos sin frames → cerrar

    # Cola exclusiva de este cliente (maxsize=1: siempre el frame IA más reciente)
    q: asyncio.Queue = asyncio.Queue(maxsize=1)
    _ai_subs.setdefault(camera_id, []).append(q)

    # Si ya hay un frame IA cacheado, enviarlo al instante
    cached = camera_stats['latest_frames'].get(camera_id)
    if cached:
        try: q.put_nowait(cached)
        except Exception: pass

    async def mjpeg_ai_generator():
        last_frame_time = time.time()
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    frame_bytes = await asyncio.wait_for(q.get(), timeout=2.0)
                    last_frame_time = time.time()
                    yield (
                        b"--" + BOUNDARY + b"\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" +
                        frame_bytes +
                        b"\r\n"
                    )
                except asyncio.TimeoutError:
                    if time.time() - last_frame_time > NO_FRAME_TIMEOUT:
                        break
        except asyncio.CancelledError:
            pass
        finally:
            try: _ai_subs.get(camera_id, []).remove(q)
            except ValueError: pass

    return StreamingResponse(
        mjpeg_ai_generator(),
        media_type=f"multipart/x-mixed-replace; boundary={BOUNDARY.decode()}",
        headers={"Cache-Control": "no-cache, no-store", "X-Accel-Buffering": "no"},
    )


@router.get("/search/items")
async def search_items(
    camera_id: str = None,
    type: str = None,          # 'person', 'vehicle', o None = todos
    limit: int = 50,
    offset: int = 0,
    min_confidence: float = 0.0
):
    """Buscar items detectados (personas y/o vehículos) en BD."""
    db = next(get_db())
    try:
        query = db.query(DetectedItem)
        if camera_id and camera_id in _camera_db_id_cache:
            query = query.filter(DetectedItem.camera_id == _camera_db_id_cache[camera_id])
        if type in ('person', 'vehicle'):
            query = query.filter(DetectedItem.type == type)
        if min_confidence > 0:
            query = query.filter(DetectedItem.confidence >= min_confidence)
        total = query.count()
        records = query.order_by(DetectedItem.detected_at.desc()).offset(offset).limit(limit).all()
        cam_name_map = {v: k for k, v in _camera_db_id_cache.items()}
        return {
            "total": total, "offset": offset, "limit": limit,
            "results": [
                {
                    "id": r.id,
                    "camera_id": r.camera_id,
                    "item_id": r.item_id,
                    "type": r.type,
                    "label": r.label,
                    "confidence": r.confidence,
                    "times_detected": r.times_detected,
                    "detected_at": r.detected_at.isoformat() if r.detected_at else None,
                    "image_path": r.image_path or _find_session_frame(
                        cam_name_map.get(r.camera_id, ''),
                        r.detected_at
                    )
                }
                for r in records
            ]
        }
    finally:
        db.close()


@router.get("/search/persons")
async def search_persons(camera_id: str = None, limit: int = 50, offset: int = 0, min_confidence: float = 0.0):
    """Compatibilidad: proxy a /search/items?type=person"""
    return await search_items(camera_id=camera_id, type='person', limit=limit, offset=offset, min_confidence=min_confidence)


@router.get("/search/vehicles")
async def search_vehicles(camera_id: str = None, limit: int = 50, offset: int = 0, min_confidence: float = 0.0):
    """Compatibilidad: proxy a /search/items?type=vehicle"""
    return await search_items(camera_id=camera_id, type='vehicle', limit=limit, offset=offset, min_confidence=min_confidence)


@router.get("/search/summary")
async def detections_summary():
    """Resumen global de detecciones en BD"""
    db = next(get_db())
    try:
        total_persons = db.query(DetectedItem).filter(DetectedItem.type == 'person').count()
        total_vehicles = db.query(DetectedItem).filter(DetectedItem.type == 'vehicle').count()
        last_person = db.query(DetectedItem).filter(DetectedItem.type == 'person').order_by(DetectedItem.detected_at.desc()).first()
        last_vehicle = db.query(DetectedItem).filter(DetectedItem.type == 'vehicle').order_by(DetectedItem.detected_at.desc()).first()
        return {
            "persons": {
                "total": total_persons,
                "last_detected_at": last_person.detected_at.isoformat() if last_person else None
            },
            "vehicles": {
                "total": total_vehicles,
                "last_detected_at": last_vehicle.detected_at.isoformat() if last_vehicle else None
            }
        }
    finally:
        db.close()


@router.get("/server/stats")
async def server_stats():
    """Estadísticas en tiempo real del servidor: CPU, RAM, red, disco."""
    import psutil, threading, time
    cpu = psutil.cpu_percent(interval=0.2)
    cpu_count = psutil.cpu_count(logical=True)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    net = psutil.net_io_counters()
    disk_io = psutil.disk_io_counters()
    proc = psutil.Process()
    proc_mem = proc.memory_info()
    proc_cpu = proc.cpu_percent(interval=None)
    uptime_sec = int(time.time() - psutil.boot_time())
    queue_info = {cid: q.qsize() for cid, q in _frame_queues.items()}
    return {
        "cpu": {
            "percent": cpu,
            "cores": cpu_count,
            "threads": threading.active_count()
        },
        "ram": {
            "total_mb": round(mem.total / 1024**2),
            "used_mb": round(mem.used / 1024**2),
            "available_mb": round(mem.available / 1024**2),
            "percent": mem.percent
        },
        "process": {
            "ram_mb": round(proc_mem.rss / 1024**2),
            "ram_vms_mb": round(proc_mem.vms / 1024**2),
            "cpu_percent": round(proc_cpu, 1)
        },
        "disk": {
            "total_gb": round(disk.total / 1024**3, 1),
            "used_gb": round(disk.used / 1024**3, 1),
            "free_gb": round(disk.free / 1024**3, 1),
            "percent": disk.percent,
            "io_read_mb": round(disk_io.read_bytes / 1024**2, 1) if disk_io else 0,
            "io_write_mb": round(disk_io.write_bytes / 1024**2, 1) if disk_io else 0
        },
        "network": {
            "sent_mb": round(net.bytes_sent / 1024**2, 1),
            "recv_mb": round(net.bytes_recv / 1024**2, 1),
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv
        },
        "cameras": {
            "active": len(camera_stats['active_cameras']),
            "frames_received": camera_stats['frames_received'],
            "bytes_received_mb": round(camera_stats['bytes_received'] / 1024**2, 1),
            "queue_pending": queue_info
        },
        "uptime_sec": uptime_sec
    }


async def get_camera_config():
    """Obtener configuración de red (IP pública, local y puertos) para clientes remotos"""
    public_ip = await get_public_ip_async()
    local_ip = get_local_ip()
    
    # Usar router_port si está configurado, sino usar public_port
    remote_port = settings.router_port or settings.public_port
    local_port = settings.public_port
    
    upload_endpoint = "/api/v2/camera/upload"
    
    return {
        # IP Pública (acceso remoto)
        "public_ip": public_ip,
        "router_port": remote_port,
        "remote_url": f"http://{public_ip}:{remote_port}",
        "remote_upload_url": f"http://{public_ip}:{remote_port}{upload_endpoint}",
        
        # IP Local (acceso en la red local)
        "local_ip": local_ip,
        "local_port": local_port,
        "local_url": f"http://{local_ip}:{local_port}",
        "local_upload_url": f"http://{local_ip}:{local_port}{upload_endpoint}",
        
        # Legacy fields para compatibilidad
        "public_port": remote_port,
        "server_url": f"http://{public_ip}:{remote_port}",
        "upload_endpoint": upload_endpoint
    }


@router.get("/camera-client", response_class=HTMLResponse)
async def camera_client_page():
    """Página web con información de conectividad para clientes"""
    
    # Obtener IPs y puertos del servidor
    try:
        public_ip = await get_public_ip_async()
    except:
        public_ip = settings.public_ip
    
    local_ip = get_local_ip()
    remote_port = settings.router_port or settings.public_port
    local_port = settings.public_port
    
    # Construir URLs
    remote_connection = f"{public_ip}:{remote_port}"
    local_connection = f"{local_ip}:{local_port}"
    
    # HTML template
    html_content = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Conectar cliente</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a3a52 0%, #2c5aa0 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 500px;
            width: 100%;
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #1a3a52 0%, #2c5aa0 100%);
            color: white;
            padding: 30px 25px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 24px;
            margin-bottom: 8px;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 14px;
        }
        
        .content {
            padding: 30px 25px;
        }
        
        .connection-group {
            margin-bottom: 25px;
        }
        
        .connection-title {
            color: #1a3a52;
            font-weight: 700;
            font-size: 14px;
            text-transform: uppercase;
            margin-bottom: 12px;
            letter-spacing: 0.5px;
        }
        
        .connection-value {
            background: #f5f7fa;
            border-left: 4px solid #2c5aa0;
            padding: 15px;
            border-radius: 6px;
            color: #1a3a52;
            font-family: 'Courier New', monospace;
            font-size: 16px;
            word-break: break-all;
            line-height: 1.6;
            font-weight: 600;
        }
        
        .copy-btn {
            background: #2c5aa0;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-top: 10px;
            transition: all 0.3s ease;
            font-weight: 600;
            width: 100%;
        }
        
        .copy-btn:hover {
            background: #1a3a52;
            transform: translateY(-1px);
        }
        
        .footer {
            padding: 20px 25px;
            background: #f5f7fa;
            text-align: center;
            color: #666;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Conectar cliente</h1>
            <p>Información de Conexión</p>
        </div>
        
        <div class="content">
            <div class="connection-group">
                <div class="connection-title">ACCESO REMOTO</div>
                <div class="connection-value" id="remote">REMOTE_IP_PLACEHOLDER</div>
                <button class="copy-btn" type="button" onclick="copy('remote')">Copiar</button>
            </div>
            
            <div class="connection-group">
                <div class="connection-title">ACCESO LOCAL</div>
                <div class="connection-value" id="local">LOCAL_IP_PLACEHOLDER</div>
                <button class="copy-btn" type="button" onclick="copy('local')">Copiar</button>
            </div>
        </div>
        
        <div class="footer">
            Usa cualquiera de estas direcciones para conectar tus clientes
        </div>
    </div>
    
    <script>
        function copy(id) {
            var elem = document.getElementById(id);
            var text = elem.textContent;
            navigator.clipboard.writeText(text).then(function() {
                alert('Copiado: ' + text);
            }, function() {
                alert('Error al copiar');
            });
        }
    </script>
</body>
</html>"""
    
    # Reemplazar placeholders
    html_content = html_content.replace("REMOTE_IP_PLACEHOLDER", remote_connection)
    html_content = html_content.replace("LOCAL_IP_PLACEHOLDER", local_connection)
    
    return HTMLResponse(content=html_content)
