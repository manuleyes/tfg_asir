"""
Resumen de sesión: guarda la mejor captura por persona/vehículo único.

Estructura de salida:
    session_dir/
        frames/          ← todos los frames YOLO anotados
        resumen/
            personas/    ← mejor crop por persona única (deduplicado por cara)
            vehiculos/   ← mejor crop por vehículo único (deduplicado por histograma)

Dependencias:
  - cv2 (siempre disponible)
  - DeepFace (opcional, mejora mucho la deduplicación facial)
  - numpy (siempre disponible)
"""

import os
import cv2
import numpy as np
import logging
import threading
from datetime import datetime

logger = logging.getLogger(__name__)

# ── DeepFace (opcional) ───────────────────────────────────────────────────────
try:
    from deepface import DeepFace as _DF
    _DEEPFACE_OK = True
    logger.info("[Summary] DeepFace disponible — reconocimiento facial activado")
except ImportError:
    _DEEPFACE_OK = False
    logger.warning("[Summary] DeepFace no disponible — deduplicación facial por histograma")

# ── Haar cascade (viene con cualquier opencv) ─────────────────────────────────
_FACE_CASCADE = None
_CASCADE_LOCK = threading.Lock()

def _get_face_cascade():
    global _FACE_CASCADE
    if _FACE_CASCADE is None:
        with _CASCADE_LOCK:
            if _FACE_CASCADE is None:
                path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                _FACE_CASCADE = cv2.CascadeClassifier(path)
    return _FACE_CASCADE


# ─────────────────────────────────────────────────────────────────────────────
class SessionSummary:
    """
    Estado en memoria para una sesión de cámara.
    Diseñado para usarse desde un único hilo (ThreadPoolExecutor con 1 worker).
    """

    FACE_DIST_THRESHOLD    = 0.45   # < umbral coseno → misma persona
    VEHICLE_HIST_THRESHOLD = 0.90   # > correlación  → mismo vehículo
    MIN_CROP_SIDE          = 40     # píxeles mínimos en cada lado del crop

    def __init__(self, session_dir: str):
        self.session_dir  = session_dir
        self.frames_dir   = os.path.join(session_dir, 'frames')
        self.persons_dir  = os.path.join(session_dir, 'resumen', 'personas')
        self.vehicles_dir = os.path.join(session_dir, 'resumen', 'vehiculos')
        for d in (self.frames_dir, self.persons_dir, self.vehicles_dir):
            os.makedirs(d, exist_ok=True)

        # Registro en memoria
        # personas: [{'embedding': ndarray|None, 'hist': ndarray, 'confidence': float, 'path': str}]
        self._persons:  list = []
        # vehículos: [{'hist': ndarray, 'confidence': float, 'path': str}]
        self._vehicles: list = []

        self._person_counter  = 0
        self._vehicle_counter = 0

    # ── Helpers de cara ───────────────────────────────────────────────────────

    def _detect_face_in_crop(self, person_crop: np.ndarray):
        """Localiza cara con Haar cascade. Devuelve crop de cara o None."""
        gray = cv2.cvtColor(person_crop, cv2.COLOR_BGR2GRAY)
        cascade = _get_face_cascade()
        h, w = person_crop.shape[:2]

        # Buscar primero en la mitad superior
        upper = gray[:max(1, h // 2), :]
        faces = cascade.detectMultiScale(upper, scaleFactor=1.1, minNeighbors=4,
                                         minSize=(28, 28))
        offset_y = 0
        if len(faces) == 0:
            faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3,
                                             minSize=(24, 24))
            offset_y = 0
        else:
            offset_y = 0  # coordenadas en upper, que empieza en y=0

        if len(faces) == 0:
            return None

        # La cara más grande
        faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
        x, y, fw, fh = faces[0]
        y_abs = y + offset_y
        face = person_crop[y_abs: y_abs + fh, x: x + fw]
        if face.size == 0:
            return None
        return face

    def _get_face_embedding(self, face_crop: np.ndarray):
        """Extrae embedding con DeepFace (Facenet). Devuelve ndarray o None."""
        if not _DEEPFACE_OK:
            return None
        try:
            result = _DF.represent(
                face_crop,
                model_name='Facenet',        # ligero y rápido
                enforce_detection=False,
                detector_backend='skip',     # ya tenemos el crop de cara
            )
            if result:
                return np.array(result[0]['embedding'], dtype=np.float32)
        except Exception as e:
            logger.debug(f"[Summary] DeepFace represent: {e}")
        return None

    @staticmethod
    def _cosine_dist(a: np.ndarray, b: np.ndarray) -> float:
        na = np.linalg.norm(a) + 1e-9
        nb = np.linalg.norm(b) + 1e-9
        dot = float(np.dot(a / na, b / nb))
        return float(np.arccos(np.clip(dot, -1.0, 1.0)) / np.pi)

    # ── Helpers de histograma ─────────────────────────────────────────────────

    @staticmethod
    def _compute_hist(crop: np.ndarray) -> np.ndarray:
        """Histograma HSV 16×16 bins, aplanado y normalizado."""
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        h = cv2.calcHist([hsv], [0, 1], None, [16, 16], [0, 180, 0, 256])
        cv2.normalize(h, h, 0, 1, cv2.NORM_MINMAX)
        return h.flatten()

    @staticmethod
    def _hist_corr(h1: np.ndarray, h2: np.ndarray) -> float:
        """Correlación de Pearson entre dos histogramas."""
        c = np.corrcoef(h1, h2)
        return float(c[0, 1]) if c.shape == (2, 2) else 0.0

    # ── Crop helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _safe_crop(frame: np.ndarray, bbox: dict):
        """Recorta bbox del frame con clipping de bordes. Devuelve crop o None."""
        h, w = frame.shape[:2]
        x1 = max(0, int(bbox['x1']))
        y1 = max(0, int(bbox['y1']))
        x2 = min(w, int(bbox['x2']))
        y2 = min(h, int(bbox['y2']))
        if x2 - x1 < SessionSummary.MIN_CROP_SIDE or y2 - y1 < SessionSummary.MIN_CROP_SIDE:
            return None
        return frame[y1:y2, x1:x2].copy()

    @staticmethod
    def _plate_area(car_crop: np.ndarray) -> np.ndarray:
        """Recorta zona inferior del vehículo donde suele estar la matrícula."""
        h = car_crop.shape[0]
        return car_crop[int(h * 0.60): int(h * 0.90), :]

    # ── Guardar imágenes ──────────────────────────────────────────────────────

    def _save_person_img(self, person_crop: np.ndarray, face_crop, confidence: float, path: str):
        img = person_crop.copy()
        label = f"Conf: {int(confidence * 100)}%"
        cv2.putText(img, label, (4, 18), cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, (50, 255, 50), 1, cv2.LINE_AA)
        if face_crop is not None:
            # Miniatura de cara en esquina superior derecha
            th = min(60, img.shape[0] // 3)
            tw = min(60, img.shape[1] // 3)
            try:
                thumb = cv2.resize(face_crop, (tw, th))
                y_off = 2
                x_off = img.shape[1] - tw - 2
                img[y_off:y_off + th, x_off:x_off + tw] = thumb
                cv2.rectangle(img, (x_off, y_off), (x_off + tw, y_off + th),
                              (50, 255, 50), 1)
            except Exception:
                pass
        cv2.imwrite(path, img)

    def _save_vehicle_img(self, car_crop: np.ndarray, confidence: float, path: str):
        plate = self._plate_area(car_crop)
        h_car, w_car = car_crop.shape[:2]
        # Separador amarillo
        sep = np.full((3, w_car, 3), (0, 200, 255), dtype=np.uint8)
        h_pl = plate.shape[0]
        if plate.shape[1] != w_car:
            plate = cv2.resize(plate, (w_car, h_pl))
        composite = np.vstack([car_crop, sep, plate])
        cv2.putText(composite, f"Conf: {int(confidence * 100)}%", (4, 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 200, 255), 1, cv2.LINE_AA)
        cv2.putText(composite, "Zona matricula v", (4, h_car + 3 + 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 200, 255), 1, cv2.LINE_AA)
        cv2.imwrite(path, composite)

    # ── API pública ───────────────────────────────────────────────────────────

    def process_person(self, raw_frame: np.ndarray, bbox: dict, confidence: float):
        """
        Analiza un bounding box de persona.
        Guarda o actualiza en resumen/personas/ si es nueva o de mayor confianza.
        """
        try:
            person_crop = self._safe_crop(raw_frame, bbox)
            if person_crop is None:
                return

            face_crop = self._detect_face_in_crop(person_crop)
            face_for_emb = face_crop if face_crop is not None else person_crop

            embedding = self._get_face_embedding(face_for_emb)
            # Histograma como fallback de deduplicación
            hist = self._compute_hist(person_crop)

            if self._persons:
                if embedding is not None and self._persons[0]['embedding'] is not None:
                    # Deduplicar por embedding (DeepFace)
                    dists = [self._cosine_dist(embedding, p['embedding'])
                             for p in self._persons if p['embedding'] is not None]
                    best_idx = int(np.argmin(dists))
                    if dists[best_idx] < self.FACE_DIST_THRESHOLD:
                        # Persona conocida
                        if confidence > self._persons[best_idx]['confidence']:
                            self._persons[best_idx]['confidence'] = confidence
                            self._persons[best_idx]['embedding'] = embedding
                            self._save_person_img(person_crop, face_crop, confidence,
                                                  self._persons[best_idx]['path'])
                        return
                else:
                    # Fallback: histograma
                    corrs = [self._hist_corr(hist, p['hist']) for p in self._persons]
                    best_idx = int(np.argmax(corrs))
                    if corrs[best_idx] >= self.FACE_DIST_THRESHOLD:  # reutilizo var
                        if confidence > self._persons[best_idx]['confidence']:
                            self._persons[best_idx]['confidence'] = confidence
                            self._save_person_img(person_crop, face_crop, confidence,
                                                  self._persons[best_idx]['path'])
                        return

            # Persona nueva
            self._person_counter += 1
            ts = datetime.now().strftime('%H-%M-%S')
            filename = f"p{self._person_counter:03d}_conf{int(confidence * 100):02d}_{ts}.jpg"
            path = os.path.join(self.persons_dir, filename)
            self._save_person_img(person_crop, face_crop, confidence, path)
            self._persons.append({
                'embedding': embedding,
                'hist': hist,
                'confidence': confidence,
                'path': path,
            })
        except Exception as e:
            logger.debug(f"[Summary] process_person error: {e}")

    def process_vehicle(self, raw_frame: np.ndarray, bbox: dict, confidence: float):
        """
        Analiza un bounding box de vehículo.
        Guarda o actualiza en resumen/vehiculos/ si es nuevo o de mayor confianza.
        """
        try:
            car_crop = self._safe_crop(raw_frame, bbox)
            if car_crop is None:
                return

            hist = self._compute_hist(car_crop)

            if self._vehicles:
                corrs = [self._hist_corr(hist, v['hist']) for v in self._vehicles]
                best_idx = int(np.argmax(corrs))
                if corrs[best_idx] >= self.VEHICLE_HIST_THRESHOLD:
                    # Vehículo conocido
                    if confidence > self._vehicles[best_idx]['confidence']:
                        self._vehicles[best_idx]['confidence'] = confidence
                        self._vehicles[best_idx]['hist'] = hist
                        self._save_vehicle_img(car_crop, confidence,
                                               self._vehicles[best_idx]['path'])
                    return

            # Vehículo nuevo
            self._vehicle_counter += 1
            ts = datetime.now().strftime('%H-%M-%S')
            filename = f"v{self._vehicle_counter:03d}_conf{int(confidence * 100):02d}_{ts}.jpg"
            path = os.path.join(self.vehicles_dir, filename)
            self._save_vehicle_img(car_crop, confidence, path)
            self._vehicles.append({
                'hist': hist,
                'confidence': confidence,
                'path': path,
            })
        except Exception as e:
            logger.debug(f"[Summary] process_vehicle error: {e}")

    def stats(self) -> dict:
        return {
            'unique_persons': len(self._persons),
            'unique_vehicles': len(self._vehicles),
        }


# ── Registro global: session_dir → SessionSummary ────────────────────────────
_registry: dict = {}
_registry_lock = threading.Lock()


def get_session_summary(session_dir: str) -> SessionSummary:
    """Obtiene (creándolo si es necesario) el SessionSummary para una sesión."""
    if session_dir not in _registry:
        with _registry_lock:
            if session_dir not in _registry:
                _registry[session_dir] = SessionSummary(session_dir)
    return _registry[session_dir]
