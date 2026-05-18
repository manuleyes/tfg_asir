"""
Integration Pipeline - FASES 1-2 Combined
Combines: TensorRT YOLO + Face Recognition

Pipeline completo para detección y re-ID
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import time
from collections import deque

logger = logging.getLogger(__name__)

# Import FASE 1, 2, 3
try:
    from .yolo_optimized import get_yolo_detector, OptimizedYOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("️ YOLO module not available")

try:

    from .face_recognition import (
        get_face_recognizer,
        get_person_reidentifier,
        FaceRecognizer,
        PersonReIdentifier
    )
    FACE_AVAILABLE = True
except ImportError:
    FACE_AVAILABLE = False
    logger.warning("️ Face recognition not available")


@dataclass
class DetectionResult:
    """Resultado de detección YOLO"""
    
    class_id: int
    class_name: str
    confidence: float
    bbox: Dict  # {'x1', 'y1', 'x2', 'y2'}
    frame_id: int
    timestamp: float
    
    # FASE 2 - Face Recognition
    face_detected: bool = False
    person_id: Optional[str] = None
    face_confidence: float = 0.0
    watch_list_match: Optional[Dict] = None


@dataclass
class FrameAnalysis:
    """Análisis completo de frame"""
    
    frame_id: int
    camera_id: str
    timestamp: float
    detections: List[DetectionResult]
    anomalies: List[Dict]
    alerts: List[Dict]
    stats: Dict
    processing_time_ms: float
    
    def to_dict(self) -> Dict:
        """Convertir a dict para JSON"""
        return {
            'frame_id': self.frame_id,
            'camera_id': self.camera_id,
            'timestamp': self.timestamp,
            'detections': [self._det_to_dict(d) for d in self.detections],
            'anomalies': self.anomalies,
            'alerts': self.alerts,
            'stats': self.stats,
            'processing_time_ms': self.processing_time_ms
        }
    
    @staticmethod
    def _det_to_dict(det: DetectionResult) -> Dict:
        """Convert detection to dict"""
        return {
            'class_id': det.class_id,
            'class_name': det.class_name,
            'confidence': float(det.confidence),
            'bbox': det.bbox,
            'person_id': det.person_id,
            'face_confidence': float(det.face_confidence),
            'watch_list_match': det.watch_list_match
        }


class SurveillancePipeline:
    """
    Pipeline de vigilancia completo
    
    FASE 1: Fast detection (YOLO)
    FASE 2: Face recognition + Re-ID
    """
    
    def __init__(
        self,
        camera_id: str = 'CAM_1',
        enable_faces: bool = True,
        enable_retracking: bool = True,
        anomaly_buffer_size: int = 30
    ):
        """
        Args:
            camera_id: ID de cámara
            enable_faces: Activar face recognition
            enable_retracking: Activar person re-id
            anomaly_buffer_size: Buffer para anómalos
        """
        
        self.camera_id = camera_id
        self.enable_faces = enable_faces and FACE_AVAILABLE
        self.enable_retracking = enable_retracking and FACE_AVAILABLE
        
        # Initialize components
        self.yolo = get_yolo_detector() if YOLO_AVAILABLE else None
        self.face_recognizer = get_face_recognizer() if self.enable_faces else None
        self.reidentifier = get_person_reidentifier() if self.enable_retracking else None
        
        # Stats
        self.frame_count = 0
        self.anomaly_buffer = deque(maxlen=anomaly_buffer_size)
        self.processed_times = deque(maxlen=100)  # Last 100 frames
        
        logger.info(f" Pipeline initialized for {camera_id}")
        logger.info(f"   YOLO: {'ON' if self.yolo else 'OFF'}")
        logger.info(f"   Faces: {'ON' if self.face_recognizer else 'OFF'}")
        logger.info(f"   Re-ID: {'ON' if self.reidentifier else 'OFF'}")
    
    def process_frame(
        self,
        frame: np.ndarray,
        zone_polygon: Optional[List] = None,
        return_annotated: bool = False
    ) -> Tuple[FrameAnalysis, Optional[np.ndarray]]:
        """
        Procesar frame completo
        
        Returns:
            (FrameAnalysis, annotated_frame_or_None)
        """
        
        start_time = time.time()
        self.frame_count += 1
        
        detections = []
        anomalies = []
        alerts = []
        
        # ======= FASE 1: YOLO Detection =======
        if not self.yolo:
            logger.error(" YOLO not available")
            return None, None
        
        try:
            yolo_results = self.yolo.infer(frame)
            logger.info(f" YOLO detected {len(yolo_results)} objects")
        
        except Exception as e:
            logger.error(f" YOLO error: {e}")
            yolo_results = []
        
        # ======= Convert YOLO results =======
        for result in yolo_results:
            det = DetectionResult(
                class_id=int(result.get('class_id', 0)),
                class_name=result.get('class_name', 'unknown'),
                confidence=float(result.get('confidence', 0)),
                bbox=result.get('bbox', {}),
                frame_id=self.frame_count,
                timestamp=time.time()
            )
            detections.append(det)
        
        # ======= FASE 2: Face Recognition =======
        if self.enable_faces and self.face_recognizer:
            try:
                for det in detections:
                    # Only process persons
                    if det.class_name not in ['person', 'person_detected']:
                        continue
                    
                    # Extract face embedding
                    embedding = self.face_recognizer.get_embedding(frame, det.bbox)
                    
                    if embedding:
                        det.face_detected = True
                        
                        # Check watch-list
                        watch_alert = self.face_recognizer.detect_watch_list(
                            embedding,
                            camera_id=self.camera_id
                        )
                        
                        if watch_alert:
                            det.watch_list_match = watch_alert
                            det.person_id = watch_alert['person_id']
                            det.face_confidence = watch_alert['confidence']
                            
                            alerts.append(watch_alert)
                            logger.warning(f"🚨 WATCH LIST MATCH: {det.person_id}")
                        
                        else:
                            # Try to identify from known persons
                            match = self.face_recognizer.identify_person(embedding)
                            
                            if match:
                                person_id, confidence = match
                                det.person_id = person_id
                                det.face_confidence = confidence
                                
                                # Track cross-camera
                                self.face_recognizer.track_person(
                                    person_id,
                                    embedding,
                                    self.camera_id
                                )
            
            except Exception as e:
                logger.warning(f"️ Face recognition error: {e}")
        
        # ======= Build response =======
        processing_time = (time.time() - start_time) * 1000  # ms
        self.processed_times.append(processing_time)
        
        stats = {
            'frame_id': self.frame_count,
            'detections': len(detections),
            'anomalies': len(anomalies),
            'alerts': len(alerts),
            'faces_detected': sum(1 for d in detections if d.face_detected),
            'avg_processing_time_ms': float(np.mean(list(self.processed_times))),
            'yolo_stats': self.yolo.get_stats() if self.yolo else {},
            'face_stats': self.face_recognizer.get_stats() if self.face_recognizer else {}
        }
        
        analysis = FrameAnalysis(
            frame_id=self.frame_count,
            camera_id=self.camera_id,
            timestamp=time.time(),
            detections=detections,
            anomalies=anomalies,
            alerts=alerts,
            stats=stats,
            processing_time_ms=processing_time
        )
        
        # Annotate if requested
        annotated_frame = None
        if return_annotated:
            try:
                import cv2
                annotated_frame = self._annotate_frame(frame, analysis)
            except Exception as e:
                logger.warning(f"️ Annotation error: {e}")
        
        return analysis, annotated_frame
    
    def _annotate_frame(self, frame: np.ndarray, analysis: FrameAnalysis) -> np.ndarray:
        """Anotar frame con detecciones y alertas"""
        try:
            import cv2
        except:
            return frame
        
        annotated = frame.copy()
        h, w = frame.shape[:2]
        
        for det in analysis.detections:
            # Draw bbox
            x1, y1 = int(det.bbox['x1']), int(det.bbox['y1'])
            x2, y2 = int(det.bbox['x2']), int(det.bbox['y2'])
            
            # Color based on alert
            color = (0, 255, 0)  # Green by default
            if det.watch_list_match:
                color = (0, 165, 255)  # Orange
            
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            # Label
            label = f"{det.class_name} {det.confidence:.2f}"
            if det.person_id:
                label += f" ID:{det.person_id}"
            
            cv2.putText(
                annotated,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2
            )
        
        # Frame info
        info = f"Frame: {analysis.frame_id} | Det: {len(analysis.detections)} | Anom: {len(analysis.anomalies)} | Alerts: {len(analysis.alerts)} | {analysis.processing_time_ms:.1f}ms"
        cv2.putText(
            annotated,
            info,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )
        
        return annotated
    
    def batch_process(
        self,
        frames: List[np.ndarray],
        batch_size: int = 16
    ) -> List[FrameAnalysis]:
        """Procesar múltiples frames en batch"""
        
        results = []
        
        # Use YOLO batch mode if available
        if self.yolo and hasattr(self.yolo, 'infer_batch'):
            try:
                batch_results = self.yolo.infer_batch(frames, batch_size=batch_size)
                logger.info(f" Batch processed {len(frames)} frames")
                
                # Process each frame with behavior/faces
                for i, frame in enumerate(frames):
                    analysis, _ = self.process_frame(frame)
                    if analysis:
                        results.append(analysis)
            
            except Exception as e:
                logger.warning(f"️ Batch processing error: {e}")
                # Fallback to sequential
                for frame in frames:
                    analysis, _ = self.process_frame(frame)
                    if analysis:
                        results.append(analysis)
        
        else:
            # Sequential processing
            for frame in frames:
                analysis, _ = self.process_frame(frame)
                if analysis:
                    results.append(analysis)
        
        return results
    
    def get_summary(self) -> Dict:
        """Obtener resumen de la pipeline"""
        
        total_anomalies = len(self.anomaly_buffer)
        
        return {
            'camera_id': self.camera_id,
            'frames_processed': self.frame_count,
            'total_anomalies_detected': total_anomalies,
            'avg_processing_time_ms': float(np.mean(list(self.processed_times))) if self.processed_times else 0,
            'yolo_enabled': bool(self.yolo),
            'faces_enabled': self.enable_faces,
            'retracking_enabled': self.enable_retracking
        }


# Singleton
_pipeline: Optional[SurveillancePipeline] = None

def get_surveillance_pipeline(camera_id: str = 'CAM_1') -> SurveillancePipeline:
    """Get o crear pipeline"""
    global _pipeline
    
    if _pipeline is None:
        _pipeline = SurveillancePipeline(
            camera_id=camera_id,
            enable_faces=True,
            enable_retracking=True
        )
    
    return _pipeline
