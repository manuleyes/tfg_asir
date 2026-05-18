"""
Unit Tests para FASE 1: YOLO Detection (TensorRT)
Valida:
- Inicialización del detector
- Inference en single frame
- Batch processing
- Stats y caching
"""

import pytest
import numpy as np
import cv2
from typing import Dict
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.services.yolo_optimized import OptimizedYOLO, get_yolo_detector


class TestOptimizedYOLOInitialization:
    """Test inicialización del detector"""
    
    def test_detector_creates_without_error(self):
        """Debe crear instancia sin errores"""
        detector = OptimizedYOLO(device="cpu")
        assert detector is not None
        assert detector.device == "cpu"
        assert detector.enable_caching == True
    
    def test_detector_lazy_loads_model(self):
        """Modelo debe estar None hasta primer uso"""
        detector = OptimizedYOLO(device="cpu")
        assert detector.model is None or detector._model_loaded == False
    
    def test_detector_has_correct_defaults(self):
        """Debe tener valores por defecto correctos"""
        detector = OptimizedYOLO()
        assert detector.batch_size == 1
        assert detector.conf_threshold == 0.5
        assert detector.inference_times == []
        assert detector.frame_count == 0


class TestOptimizedYOLOInference:
    """Test inference del detector"""
    
    @pytest.fixture
    def test_frame(self):
        """Crear frame de prueba (640x480 RGB)"""
        return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    @pytest.fixture
    def detector(self):
        """Inicializar detector"""
        return OptimizedYOLO(device="cpu", enable_caching=False)
    
    def test_infer_returns_dict(self, detector, test_frame):
        """Inference debe retornar Dict"""
        result = detector.infer(test_frame)
        assert isinstance(result, dict)
        assert 'detections' in result
        assert 'inference_time' in result
    
    def test_infer_detections_is_list(self, detector, test_frame):
        """Detections debe ser list"""
        result = detector.infer(test_frame)
        assert isinstance(result['detections'], list)
    
    def test_infer_inference_time_is_float(self, detector, test_frame):
        """Inference time debe ser float >= 0"""
        result = detector.infer(test_frame)
        assert isinstance(result['inference_time'], (int, float))
        assert result['inference_time'] >= 0
    
    def test_infer_updates_frame_count(self, detector, test_frame):
        """Cada infer debe incrementar frame_count"""
        initial_count = detector.frame_count
        detector.infer(test_frame)
        assert detector.frame_count > initial_count


class TestOptimizedYOLOBatchProcessing:
    """Test batch processing"""
    
    @pytest.fixture
    def detector(self):
        return OptimizedYOLO(device="cpu", batch_size=4)
    
    @pytest.fixture
    def test_batch(self):
        """Batch de 4 frames"""
        return [
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            for _ in range(4)
        ]
    
    def test_infer_batch_returns_list(self, detector, test_batch):
        """Batch inference debe retornar list"""
        result = detector.infer_batch(test_batch)
        assert isinstance(result, list)
        assert len(result) == len(test_batch)
    
    def test_infer_batch_each_item_is_dict(self, detector, test_batch):
        """Cada item debe ser dict con keys correctas"""
        result = detector.infer_batch(test_batch)
        for item in result:
            assert isinstance(item, dict)
            assert 'detections' in item
            assert 'inference_time' in item


class TestOptimizedYOLOCaching:
    """Test caching de resultados"""
    
    def test_caching_enabled_by_default(self):
        """Caching debe estar habilitado por defecto"""
        detector = OptimizedYOLO()
        assert detector.enable_caching == True
    
    def test_cache_stores_results(self):
        """Cache debe almacenar resultados"""
        detector = OptimizedYOLO(device="cpu", enable_caching=True)
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        result1 = detector.infer(frame)
        # Same frame should hit cache
        result2 = detector.infer(frame)
        
        # Results should be identical
        assert result1 == result2 or result1['detections'] == result2['detections']


class TestOptimizedYOLOStats:
    """Test estadísticas del detector"""
    
    def test_get_stats_returns_dict(self):
        """get_stats debe retornar dict"""
        detector = OptimizedYOLO(device="cpu")
        stats = detector.get_stats()
        assert isinstance(stats, dict)
    
    def test_get_stats_has_required_keys(self):
        """Stats debe tener keys requeridas"""
        detector = OptimizedYOLO(device="cpu")
        stats = detector.get_stats()
        required_keys = ['frames_processed', 'avg_inference_ms', 'fps']
        for key in required_keys:
            assert key in stats, f"Missing key: {key}"


class TestSingletonPattern:
    """Test patrón singleton"""
    
    def test_get_yolo_detector_returns_same_instance(self):
        """get_yolo_detector debe retornar misma instancia"""
        detector1 = get_yolo_detector()
        detector2 = get_yolo_detector()
        assert detector1 is detector2


# ═════════════════════════════════════════════════════════════════════════════
# Pytest parametrize tests
# ═════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("frame_shape", [
    (480, 640, 3),
    (720, 1280, 3),
    (240, 320, 3),
])
def test_different_frame_sizes(frame_shape):
    """Debe soportar diferentes tamaños de frame"""
    detector = OptimizedYOLO(device="cpu")
    frame = np.random.randint(0, 255, frame_shape, dtype=np.uint8)
    result = detector.infer(frame)
    assert isinstance(result, dict)
    assert 'detections' in result


@pytest.mark.parametrize("device", ["cpu"])  # Only test CPU (GPU optional)
def test_different_devices(device):
    """Debe inicializar con diferentes devices"""
    detector = OptimizedYOLO(device=device)
    assert detector.device == device


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
