"""
services/detection.py - Servicio de detección con YOLO
Detecta personas y vehículos en imágenes y videos
"""
try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False
    YOLO = None

from PIL import Image
import numpy as np
import cv2
import os
from pathlib import Path
from typing import List, Dict, Tuple
import logging
import warnings

# Suprimir warnings de PyTorch
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class DetectionService:
    """Servicio de detección de objetos con YOLOv8"""
    
    def __init__(self, model_path: str = "yolov8x.pt"):
        """
        Inicializar servicio de detección
        
        Args:
            model_path: Ruta al modelo YOLO
        """
        if not ULTRALYTICS_AVAILABLE:
            logger.warning("Ultralytics no disponible - detección deshabilitada")
            self.model = None
            return

        try:
            logger.info(f"Cargando modelo YOLO desde: {model_path}")
            
            # PyTorch 2.6 requiere weights_only=False para YOLO
            import torch
            old_torch_load = torch.load
            
            def torch_load_wrapper(f, *args, **kwargs):
                if 'weights_only' not in kwargs:
                    kwargs['weights_only'] = False
                return old_torch_load(f, *args, **kwargs)
            
            torch.load = torch_load_wrapper
            
            try:
                self.model = YOLO(model_path)
                self.model.to('cpu')
                logger.info("Modelo YOLO cargado exitosamente")
            finally:
                torch.load = old_torch_load
                
        except Exception as e:
            logger.error(f"Error cargando modelo YOLO: {e}")
            self.model = None
    
    def detect_in_image(self, image_path: str, conf: float = 0.5) -> Dict:
        """
        Detectar objetos en una imagen
        
        Args:
            image_path: Ruta de la imagen
            conf: Confianza mínima (0-1)
            
        Returns:
            Dict con resultados de detección
        """
        try:
            # Ejecutar detección
            results = self.model(image_path, conf=conf, verbose=False)
            result = results[0]
            
            detections = {
                "personas": [],
                "vehiculos": [],
                "total": 0
            }
            
            # Procesar detecciones
            if result.boxes:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    class_name = self.model.names[class_id]
                    confidence = float(box.conf[0])
                    
                    # Coordenadas
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    detection = {
                        "class": class_name,
                        "confidence": round(confidence, 3),
                        "box": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                        "area": (x2 - x1) * (y2 - y1)
                    }
                    
                    # Categorizar
                    if class_name == "person":
                        detections["personas"].append(detection)
                    elif class_name in ["car", "truck", "bus", "motorcycle", "bicycle"]:
                        detections["vehiculos"].append(detection)
                
                detections["total"] = len(detections["personas"]) + len(detections["vehiculos"])
                logger.info(f"Detección completada: {detections['total']} objetos")
            
            return detections
            
        except Exception as e:
            logger.error(f"Error en detección: {e}")
            return {"error": str(e), "personas": [], "vehiculos": [], "total": 0}
    
    def detect_in_frame(self, frame: np.ndarray, conf: float = 0.5) -> Tuple[np.ndarray, Dict]:
        """
        Detectar objetos en un frame de video
        
        Args:
            frame: Frame de OpenCV (BGR)
            conf: Confianza mínima
            
        Returns:
            Tupla (frame anotado, detecciones)
        """
        try:
            # Ejecutar detección
            results = self.model(frame, conf=conf, verbose=False)
            result = results[0]
            
            detections = {
                "personas": [],
                "vehiculos": [],
                "total": 0
            }
            
            # Dibujar en el frame
            annotated_frame = result.plot()
            
            # Procesar detecciones
            if result.boxes:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    class_name = self.model.names[class_id]
                    confidence = float(box.conf[0])
                    
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    detection = {
                        "class": class_name,
                        "confidence": round(confidence, 3),
                        "box": {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
                    }
                    
                    if class_name == "person":
                        detections["personas"].append(detection)
                    elif class_name in ["car", "truck", "bus", "motorcycle", "bicycle"]:
                        detections["vehiculos"].append(detection)
                
                detections["total"] = len(detections["personas"]) + len(detections["vehiculos"])
            
            return annotated_frame, detections
            
        except Exception as e:
            logger.error(f"Error en detección de frame: {e}")
            return frame, {"error": str(e), "personas": [], "vehiculos": [], "total": 0}
    
    def detect_in_video(self, video_path: str, conf: float = 0.5, output_path: str = None) -> Dict:
        """
        Detectar objetos en todo un video
        
        Args:
            video_path: Ruta del video
            conf: Confianza mínima
            output_path: Ruta para guardar video anotado (opcional)
            
        Returns:
            Dict con estadísticas de detecciones
        """
        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            frame_count = 0
            all_detections = {"personas": [], "vehiculos": [], "total": 0, "frames": []}
            
            # Setup salida si se solicita
            writer = None
            if output_path:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            logger.info(f"Procesando video: {total_frames} frames @ {fps} fps")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Detección
                annotated_frame, detections = self.detect_in_frame(frame, conf)
                
                # Guardar detecciones
                if detections["total"] > 0:
                    all_detections["frames"].append({
                        "frame": frame_count,
                        "detections": detections
                    })
                    all_detections["personas"] += detections["personas"]
                    all_detections["vehiculos"] += detections["vehiculos"]
                    all_detections["total"] += detections["total"]
                
                # Escribir en video salida
                if writer:
                    writer.write(annotated_frame)
                
                frame_count += 1
                if frame_count % 30 == 0:
                    logger.info(f"Procesados {frame_count}/{total_frames} frames")
            
            cap.release()
            if writer:
                writer.release()
            
            logger.info(f" Video procesado: {all_detections['total']} detecciones totales")
            return all_detections
            
        except Exception as e:
            logger.error(f"Error procesando video: {e}")
            return {"error": str(e), "personas": [], "vehiculos": [], "total": 0, "frames": []}

# Instancia global
detection_service = None

def get_detection_service() -> DetectionService:
    """Obtener instancia del servicio de detección"""
    global detection_service
    if detection_service is None:
        detection_service = DetectionService()
    return detection_service
