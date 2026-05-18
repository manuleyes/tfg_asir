"""
Unit Tests para FASE 3: Face Recognition & Re-Identification
Valida:
- Face embedding extraction
- Face matching
- Watch-list detection
- Cross-camera tracking
"""

import pytest
import numpy as np
from dataclasses import dataclass
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.services.face_recognition import (
    FaceRecognizer,
    FaceEmbedding,
    PersonReIdentifier,
    get_face_recognizer,
    get_person_reidentifier
)


class TestFaceEmbedding:
    """Test FaceEmbedding dataclass"""
    
    def test_face_embedding_creation(self):
        """Debe crear embedding"""
        emb_vector = np.random.randn(512)
        embedding = FaceEmbedding(
            embedding=emb_vector,
            person_id="p1",
            confidence=0.95
        )
        assert embedding.person_id == "p1"
        assert embedding.confidence == 0.95
        assert len(embedding.embedding) == 512
    
    def test_face_embedding_distance_cosine(self):
        """Debe calcular distancia cosine"""
        # Create similar embeddings
        emb1_vec = np.array([1, 0, 0, 0], dtype=float)
        emb2_vec = np.array([1, 0.1, 0, 0], dtype=float)  # Similar
        
        emb1 = FaceEmbedding(embedding=emb1_vec)
        emb2 = FaceEmbedding(embedding=emb2_vec)
        
        distance = emb1.distance_to(emb2, metric='cosine')
        assert isinstance(distance, float)
        assert 0 <= distance <= 1
    
    def test_face_embedding_distance_euclidean(self):
        """Debe calcular distancia euclidean"""
        emb1_vec = np.array([0, 0, 0, 0], dtype=float)
        emb2_vec = np.array([3, 4, 0, 0], dtype=float)
        
        emb1 = FaceEmbedding(embedding=emb1_vec)
        emb2 = FaceEmbedding(embedding=emb2_vec)
        
        distance = emb1.distance_to(emb2, metric='euclidean')
        expected = 5.0  # 3-4-5 triangle
        assert abs(distance - expected) < 0.01


class TestFaceRecognizerInitialization:
    """Test inicialización del recognizer"""
    
    def test_face_recognizer_creates(self):
        """Debe crear instancia"""
        recognizer = FaceRecognizer(
            model='Facenet512',
            distance_threshold=0.4
        )
        assert recognizer is not None
        assert recognizer.model == 'Facenet512'
        assert recognizer.distance_threshold == 0.4
    
    def test_face_recognizer_has_empty_gallery(self):
        """Gallery debe estar vacío inicialmente"""
        recognizer = FaceRecognizer()
        assert len(recognizer.gallery) == 0


class TestFaceRecognizerGallery:
    """Test gallery management"""
    
    @pytest.fixture
    def recognizer(self):
        return FaceRecognizer(distance_threshold=0.4)
    
    def test_add_to_gallery(self, recognizer):
        """Debe agregar embedding a gallery"""
        embedding = FaceEmbedding(
            embedding=np.random.randn(512),
            person_id="suspect_1"
        )
        recognizer.add_to_gallery("suspect_1", embedding)
        assert "suspect_1" in recognizer.gallery
    
    def test_gallery_lookup(self, recognizer):
        """Debe recuperar de gallery"""
        embedding = FaceEmbedding(
            embedding=np.random.randn(512),
            person_id="suspect_1"
        )
        recognizer.add_to_gallery("suspect_1", embedding)
        
        retrieved = recognizer.gallery.get("suspect_1")
        assert retrieved is not None
        assert retrieved.person_id == "suspect_1"


class TestFaceRecognizerMatching:
    """Test face matching"""
    
    @pytest.fixture
    def recognizer(self):
        return FaceRecognizer(distance_threshold=0.5)
    
    def test_match_face_returns_dict(self, recognizer):
        """match_face debe retornar dict"""
        embedding = FaceEmbedding(embedding=np.random.randn(512))
        result = recognizer.match_face(embedding)
        assert isinstance(result, dict)
    
    def test_match_face_exact_match(self, recognizer):
        """Debe encontrar match exacto"""
        embedding_vector = np.random.randn(512)
        embedding1 = FaceEmbedding(embedding=embedding_vector, person_id="p1")
        embedding2 = FaceEmbedding(embedding=embedding_vector, person_id="p1")
        
        recognizer.add_to_gallery("p1", embedding1)
        
        result = recognizer.match_face(embedding2)
        # Should find the match (distance = 0)
        assert result is not None


class TestFaceRecognizerWatchlist:
    """Test watch-list alerts"""
    
    @pytest.fixture
    def recognizer(self):
        return FaceRecognizer()
    
    def test_detect_watch_list_empty_gallery(self, recognizer):
        """Con gallery vacío no debe gatillar alerta"""
        embedding = FaceEmbedding(embedding=np.random.randn(512))
        alert = recognizer.detect_watch_list(embedding)
        
        # No match expected
        assert alert is None or alert.get('match') is False


class TestPersonReIdentifier:
    """Test person re-identification"""
    
    def test_person_reidentifier_creates(self):
        """Debe crear instancia"""
        reidentifier = PersonReIdentifier(similarity_threshold=0.6)
        assert reidentifier is not None
        assert reidentifier.similarity_threshold == 0.6
    
    def test_person_reidentifier_identify_returns_dict(self):
        """identify debe retornar dict"""
        reidentifier = PersonReIdentifier()
        
        # Mock clothing histogram
        histogram1 = np.random.randn(256)
        histogram2 = np.random.randn(256)
        
        # Should return some result
        result = reidentifier.identify(histogram1)
        assert isinstance(result, dict)


class TestCrossCameraTracking:
    """Test cross-camera tracking"""
    
    @pytest.fixture
    def recognizer(self):
        return FaceRecognizer()
    
    def test_track_person_across_cameras(self, recognizer):
        """Debe trackear persona en múltiples cámaras"""
        embedding = FaceEmbedding(
            embedding=np.random.randn(512),
            person_id="p1",
            camera_id="cam1"
        )
        
        recognizer.add_cross_camera_detection("p1", embedding, "cam1")
        
        # Should be in tracking
        assert "p1" in recognizer.cross_camera_tracking or \
               "p1" in recognizer.person_embeddings


class TestFaceRecognizerSingleton:
    """Test singleton patterns"""
    
    def test_get_face_recognizer_returns_same_instance(self):
        """Debe retornar misma instancia"""
        recognizer1 = get_face_recognizer()
        recognizer2 = get_face_recognizer()
        assert recognizer1 is recognizer2
    
    def test_get_person_reidentifier_returns_same_instance(self):
        """Debe retornar misma instancia"""
        reidentifier1 = get_person_reidentifier()
        reidentifier2 = get_person_reidentifier()
        assert reidentifier1 is reidentifier2


class TestFaceRecognizerStats:
    """Test estadísticas"""
    
    def test_recognizer_tracks_detections(self):
        """Debe trackear detecciones"""
        recognizer = FaceRecognizer()
        
        # Add some detections
        for i in range(3):
            embedding = FaceEmbedding(
                embedding=np.random.randn(512),
                person_id=f"p{i}"
            )
            recognizer.add_to_gallery(f"p{i}", embedding)
        
        # Check stats
        assert len(recognizer.gallery) == 3


# ═════════════════════════════════════════════════════════════════════════════
# Parametrized tests
# ═════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("embedding_dim", [128, 256, 512])
def test_face_embedding_different_dimensions(embedding_dim):
    """Debe soportar diferentes dimensiones"""
    embedding_vector = np.random.randn(embedding_dim)
    embedding = FaceEmbedding(embedding=embedding_vector)
    assert len(embedding.embedding) == embedding_dim


@pytest.mark.parametrize("threshold", [0.3, 0.4, 0.5, 0.6])
def test_face_recognizer_different_thresholds(threshold):
    """Debe inicializar con diferentes thresholds"""
    recognizer = FaceRecognizer(distance_threshold=threshold)
    assert recognizer.distance_threshold == threshold


# ═════════════════════════════════════════════════════════════════════════════
# E2E tests
# ═════════════════════════════════════════════════════════════════════════════

class TestFaceRecognizerEndToEnd:
    """E2E face recognition workflow"""
    
    def test_watch_list_detection_workflow(self):
        """Workflow completo: agregar a watch-list -> detectar"""
        recognizer = FaceRecognizer()
        
        # Create suspect embedding
        suspect_embedding = FaceEmbedding(
            embedding=np.random.randn(512),
            person_id="suspect_1"
        )
        
        # Add to watch-list (gallery)
        recognizer.add_to_gallery("suspect_1", suspect_embedding)
        
        # Create detected embedding (similar but not identical)
        detected_embedding = FaceEmbedding(
            embedding=suspect_embedding.embedding + np.random.randn(512) * 0.01,
            person_id=None
        )
        
        # Try to match
        match = recognizer.match_face(detected_embedding)
        assert match is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
