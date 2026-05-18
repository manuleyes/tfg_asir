"""
FASE 3: Face Recognition & Person Re-Identification
Seguimiento multi-cámara + watch-list alerts

Características:
- Face embedding con DeepFace
- Matching entre frames
- Watch-list detection
- Cross-camera tracking
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import time
from dataclasses import dataclass
import pickle

logger = logging.getLogger(__name__)

try:
    from deepface import DeepFace
    from deepface.commons import functions as deep_functions
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    logger.warning("️ DeepFace not available - face recognition disabled")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


@dataclass
class FaceEmbedding:
    """Embedding de rostro (vector de características)"""
    embedding: np.ndarray  # Vector 128D típicamente
    person_id: Optional[str] = None
    timestamp: float = 0
    confidence: float = 1.0
    camera_id: Optional[str] = None
    bbox: Optional[Dict] = None  # {'x1', 'y1', 'x2', 'y2'}
    
    def distance_to(self, other: 'FaceEmbedding', metric: str = 'cosine') -> float:
        """
        Distancia entre embeddings
        
        Métrica recomendada: 'cosine'
        Threshold: < 0.4 = mismo persona
        """
        
        if metric == 'cosine':
            # Cosine similarity
            A = self.embedding / np.linalg.norm(self.embedding)
            B = other.embedding / np.linalg.norm(other.embedding)
            return float(np.arccos(np.clip(np.dot(A, B), -1, 1)) / np.pi)
        
        elif metric == 'euclidean':
            return float(np.linalg.norm(self.embedding - other.embedding))
        
        return float('inf')


class FaceRecognizer:
    """
    Face recognition y re-identification
    
    - Extrae embeddings de rostros
    - Matching entre personas
    - Watch-list detection
    """
    
    def __init__(
        self,
        model: str = 'Facenet512',  # 'VGGFace', 'Facenet', 'Facenet512', etc
        distance_threshold: float = 0.4,
        detector_backend: str = 'opencv'
    ):
        """
        Args:
            model: Modelo de embedding a usar
            distance_threshold: Distancia < threshold = mismo persona
            detector_backend: 'opencv', 'retinaface', 'mtcnn', etc
        """
        
        self.model = model
        self.distance_threshold = distance_threshold
        self.detector_backend = detector_backend
        
        # Gallery de embeddings públicos (watch-list, etc)
        self.gallery: Dict[str, FaceEmbedding] = {}
        
        # Tracking histórico
        self.person_embeddings: Dict[str, List[FaceEmbedding]] = defaultdict(list)
        self.cross_camera_tracking: Dict[str, List] = defaultdict(list)  # person_id -> cameras visto
        
        if not DEEPFACE_AVAILABLE:
            logger.error(" DeepFace not available")
    
    def extract_face(
        self,
        image: np.ndarray,
        bbox: Optional[Dict] = None
    ) -> Optional[np.ndarray]:
        """
        Extraer región del rostro de imagen
        
        Args:
            image: Imagen completa o región
            bbox: {'x1', 'y1', 'x2', 'y2'} del rostro (si ya se conoce)
        
        Returns:
            Imagen del rostro o None
        """
        
        if bbox and CV2_AVAILABLE:
            try:
                x1 = int(bbox['x1'])
                y1 = int(bbox['y1'])
                x2 = int(bbox['x2'])
                y2 = int(bbox['y2'])
                
                # Agregar padding
                h, w = image.shape[:2]
                x1 = max(0, x1 - 10)
                y1 = max(0, y1 - 10)
                x2 = min(w, x2 + 10)
                y2 = min(h, y2 + 10)
                
                return image[y1:y2, x1:x2]
            
            except Exception as e:
                logger.warning(f"️ Face extraction error: {e}")
                return None
        
        return image
    
    def get_embedding(
        self,
        image: np.ndarray,
        bbox: Optional[Dict] = None
    ) -> Optional[FaceEmbedding]:
        """
        Obtener embedding de rostro
        
        Args:
            image: Imagen o región
            bbox: Bounding box si se conoce
        
        Returns:
            FaceEmbedding o None
        """
        
        if not DEEPFACE_AVAILABLE:
            logger.error(" DeepFace not available")
            return None
        
        try:
            # Extract face
            face = self.extract_face(image, bbox)
            
            if face is None:
                return None
            
            # Generate embedding
            embedding_obj = DeepFace.represent(
                face,
                model_name=self.model,
                enforce_detection=False
            )
            
            if not embedding_obj:
                return None
            
            embedding_vector = np.array(embedding_obj[0]['embedding'], dtype=np.float32)
            
            return FaceEmbedding(
                embedding=embedding_vector,
                timestamp=time.time(),
                bbox=bbox,
                confidence=1.0
            )
        
        except Exception as e:
            logger.warning(f"️ Embedding extraction error: {e}")
            return None
    
    def match_face(
        self,
        embedding: FaceEmbedding,
        against: List[FaceEmbedding] = None,
        metric: str = 'cosine'
    ) -> Optional[Tuple[str, float]]:
        """
        Matching de rostro contra gallery
        
        Returns:
            (person_id, distance) o None
        """
        
        if against is None:
            against = list(self.gallery.values())
        
        if not against:
            return None
        
        best_match = None
        best_distance = float('inf')
        
        for candidate in against:
            distance = embedding.distance_to(candidate, metric=metric)
            
            if distance < best_distance:
                best_distance = distance
                best_match = candidate.person_id
        
        if best_distance <= self.distance_threshold:
            return (best_match, best_distance)
        
        return None
    
    def add_to_gallery(
        self,
        person_id: str,
        embedding: FaceEmbedding,
        replace: bool = False
    ):
        """
        Agregar rostro a gallery (watch-list)
        
        Args:
            person_id: ID de persona
            embedding: FaceEmbedding
            replace: Reemplazar si ya existe
        """
        
        if person_id in self.gallery and not replace:
            logger.warning(f"️ Person {person_id} already in gallery")
            return
        
        embedding.person_id = person_id
        self.gallery[person_id] = embedding
        
        logger.info(f" Added to gallery: {person_id}")
    
    def detect_watch_list(
        self,
        embedding: FaceEmbedding,
        camera_id: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Detectar si rostro está en watch-list
        
        Returns:
            {'match': person_id, 'confidence': 1-distance, ...} o None
        """
        
        match = self.match_face(embedding)
        
        if match:
            person_id, distance = match
            
            alert = {
                'type': 'WATCH_LIST_ALERT',
                'person_id': person_id,
                'distance': float(distance),
                'confidence': float(1.0 - distance),
                'camera_id': camera_id,
                'timestamp': time.time()
            }
            
            logger.warning(f"🚨 WATCH LIST DETECTED: {person_id} ({distance:.3f})")
            
            return alert
        
        return None
    
    def track_person(
        self,
        person_id: str,
        embedding: FaceEmbedding,
        camera_id: str
    ):
        """
        Track persona a través de cameras
        """
        
        self.person_embeddings[person_id].append(embedding)
        
        # Limit history
        if len(self.person_embeddings[person_id]) > 100:
            self.person_embeddings[person_id].pop(0)
        
        # Track camera
        if camera_id not in self.cross_camera_tracking[person_id]:
            self.cross_camera_tracking[person_id].append(camera_id)
            logger.info(f"👤 Person {person_id} now seen in: {self.cross_camera_tracking[person_id]}")
    
    def identify_person(
        self,
        embedding: FaceEmbedding,
        known_persons: Dict[str, List[FaceEmbedding]] = None
    ) -> Optional[Tuple[str, float]]:
        """
        Identificar persona (matching contra conocidos)
        
        Returns:
            (person_id, confidence) o None
        """
        
        if known_persons is None:
            known_persons = self.person_embeddings
        
        best_match = None
        best_distance = float('inf')
        
        for person_id, embeddings in known_persons.items():
            # Compare contra todos los embeddings de persona
            for known_emb in embeddings:
                distance = embedding.distance_to(known_emb)
                
                if distance < best_distance:
                    best_distance = distance
                    best_match = person_id
        
        if best_distance <= self.distance_threshold:
            confidence = 1.0 - min(best_distance / self.distance_threshold, 1.0)
            return (best_match, confidence)
        
        return None
    
    def get_stats(self) -> Dict:
        """Obtener estadísticas"""
        
        total_persons = len(self.person_embeddings)
        total_embeddings = sum(len(embs) for embs in self.person_embeddings.values())
        watch_list_size = len(self.gallery)
        
        return {
            'total_persons_tracked': total_persons,
            'total_embeddings': total_embeddings,
            'watch_list_size': watch_list_size,
            'model': self.model,
            'distance_threshold': self.distance_threshold
        }


class PersonReIdentifier:
    """
    Person Re-ID - matching de personas entre frames/cameras
    sin depender de rostro (por si face no está visible)
    
    Usa ropa, gait, silueta, etc
    """
    
    def __init__(self, similarity_threshold: float = 0.6):
        self.similarity_threshold = similarity_threshold
        self.persons: Dict[str, Dict] = {}  # person_id -> features
    
    def extract_features(
        self,
        bbox: np.ndarray,
        image: np.ndarray
    ) -> np.ndarray:
        """
        Extraer features de persona (color de ropa, etc)
        
        Versión simple: histograma de color HSV
        """
        
        if bbox is None or image is None:
            return np.zeros(64, dtype=np.float32)
        
        try:
            x1, y1, x2, y2 = map(int, bbox)
            roi = image[y1:y2, x1:x2]
            
            # Convert to HSV
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            
            # Histograma
            hist = cv2.calcHist(
                [hsv],
                [0, 1],  # H, S
                None,
                [8, 8],  # bins
                [0, 256, 0, 256]
            )
            
            # Flatten y normalize
            hist = cv2.normalize(hist, hist).flatten()
            
            return hist.astype(np.float32)
        
        except Exception as e:
            logger.warning(f"️ Feature extraction error: {e}")
            return np.zeros(64, dtype=np.float32)
    
    def match_person(
        self,
        features: np.ndarray,
        known_features: Dict[str, np.ndarray]
    ) -> Optional[Tuple[str, float]]:
        """
        Match persona con conocidas
        """
        
        if not known_features:
            return None
        
        best_match = None
        best_similarity = 0
        
        for person_id, known in known_features.items():
            # Cosine similarity
            similarity = np.dot(features, known) / (
                np.linalg.norm(features) * np.linalg.norm(known) + 1e-6
            )
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = person_id
        
        if best_similarity >= self.similarity_threshold:
            return (best_match, best_similarity)
        
        return None


# Singletons
_face_recognizer: Optional[FaceRecognizer] = None
_person_reidentifier: Optional[PersonReIdentifier] = None

def get_face_recognizer() -> FaceRecognizer:
    """Get o crear instancia de FaceRecognizer"""
    global _face_recognizer
    
    if _face_recognizer is None:
        _face_recognizer = FaceRecognizer(
            model='Facenet512',
            distance_threshold=0.4
        )
    
    return _face_recognizer

def get_person_reidentifier() -> PersonReIdentifier:
    """Get o crear instancia de PersonReIdentifier"""
    global _person_reidentifier
    
    if _person_reidentifier is None:
        _person_reidentifier = PersonReIdentifier(similarity_threshold=0.6)
    
    return _person_reidentifier
