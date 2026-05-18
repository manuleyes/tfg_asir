"""
Servicio para dibujar overlays de detecciones YOLO en tiempo real
"""

import cv2
import numpy as np
from typing import Tuple, List, Dict
from .yolo_optimized import OptimizedYOLO

class DetectionOverlay:
    """Dibuja rectangulos y etiquetas sobre frames con detecciones"""
    
    def __init__(self):
        self.yolo = OptimizedYOLO(model_path="yolov8x.pt", device="cpu")
        self.color_yellow = (0, 255, 255)  # BGR format
        self.thickness = 2
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.person_count = 0
        self.car_count = 0
        
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Procesa frame, detecta objetos y dibuja overlays
        
        Returns:
            (frame_con_overlays, estadisticas)
        """
        try:
            # Realizar detección
            infer_result = self.yolo.infer(frame)
            results = infer_result.get('detections', []) if isinstance(infer_result, dict) else []
            
            # Resetear contadores
            self.person_count = 0
            self.car_count = 0
            events = []
            boxes = []  # [{type, confidence, x1, y1, x2, y2, label}]
            
            # Procesar detecciones
            if results:
                for detection in results:
                    class_id = detection['class_id']
                    confidence = detection['confidence']
                    
                    # Filtrar solo personas (0) y coches (2)
                    if class_id == 0:  # Persona
                        self.person_count += 1
                        label = f"Persona ({confidence:.1%})"
                        det_type = "person"
                        events.append(("person", confidence))
                    elif class_id == 2:  # Coche
                        self.car_count += 1
                        label = f"Coche ({confidence:.1%})"
                        det_type = "car"
                        events.append(("car", confidence))
                    else:
                        continue
                    
                    # Dibujar rectángulo
                    bbox = detection['bbox']
                    x1, y1, x2, y2 = bbox['x1'], bbox['y1'], bbox['x2'], bbox['y2']
                    cv2.rectangle(frame, (x1, y1), (x2, y2), self.color_yellow, self.thickness)
                    
                    # Dibujar etiqueta
                    text_size = cv2.getTextSize(label, self.font, 0.6, 1)[0]
                    cv2.rectangle(frame, 
                                (x1, y1 - 25), 
                                (x1 + text_size[0], y1), 
                                self.color_yellow, 
                                -1)
                    cv2.putText(frame, label, (x1, y1 - 5), self.font, 0.6, (0, 0, 0), 1)

                    boxes.append({
                        'type': det_type,
                        'confidence': round(float(confidence), 3),
                        'x1': int(x1), 'y1': int(y1),
                        'x2': int(x2), 'y2': int(y2),
                        'label': label
                    })
            
            # Dibujar contadores en esquina superior izquierda
            counter_text_person = f"Personas: {self.person_count}"
            counter_text_car = f"Coches: {self.car_count}"
            
            cv2.rectangle(frame, (10, 10), (300, 70), self.color_yellow, -1)
            cv2.putText(frame, counter_text_person, (20, 35), self.font, 1, (0, 0, 0), 2)
            cv2.putText(frame, counter_text_car, (20, 60), self.font, 1, (0, 0, 0), 2)
            
            return frame, {
                'persons': self.person_count,
                'cars': self.car_count,
                'events': events,
                'boxes': boxes,
                'total_detections': len(results)
            }
            
        except Exception as e:
            print(f"Error en DetectionOverlay: {e}")
            return frame, {'error': str(e)}

# Instancia global
_overlay_instance = None

def get_overlay_processor():
    """Obtener instancia global del procesador"""
    global _overlay_instance
    if _overlay_instance is None:
        _overlay_instance = DetectionOverlay()
    return _overlay_instance
