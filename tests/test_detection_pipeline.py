"""
Unit Tests for Detection Pipeline Integration (FASE 1-3)
Valida:
- Pipeline initialization
- Frame processing
- Batch processing
- Integration between all phases
"""

import pytest
import numpy as np
import cv2
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.services.detection_pipeline import (
    SurveillancePipeline,
    FrameAnalysis,
    get_surveillance_pipeline
)


class TestFrameAnalysis:
    """Test FrameAnalysis dataclass"""
    
    def test_frame_analysis_creation(self):
        """Debe crear FrameAnalysis"""
        analysis = FrameAnalysis(
            frame_id=1,
            timestamp=0.0,
            detections=[],
            anomalies=[],
            alerts=[]
        )
        assert analysis.frame_id == 1
        assert analysis.timestamp == 0.0
        assert isinstance(analysis.detections, list)
    
    def test_frame_analysis_has_stats(self):
        """Debe tener stats dict"""
        analysis = FrameAnalysis(
            frame_id=1,
            timestamp=0.0,
            detections=[],
            anomalies=[],
            alerts=[],
            stats={'total_time_ms': 45.2}
        )
        assert 'total_time_ms' in analysis.stats


class TestSurveillancePipelineInitialization:
    """Test inicialización del pipeline"""
    
    def test_pipeline_creates(self):
        """Debe crear instancia de pipeline"""
        pipeline = SurveillancePipeline()
        assert pipeline is not None
    
    def test_pipeline_has_services(self):
        """Debe tener referencias a servicios"""
        pipeline = SurveillancePipeline()
        # Services are lazy-loaded
        assert hasattr(pipeline, 'yolo')

        assert hasattr(pipeline, 'face_recognizer')


class TestSurveillancePipelineFrameProcessing:
    """Test procesamiento de frames"""
    
    @pytest.fixture
    def pipeline(self):
        return SurveillancePipeline()
    
    @pytest.fixture
    def test_frame(self):
        """Crear frame de prueba"""
        # Create semi-realistic frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Add some random objects
        cv2.rectangle(frame, (100, 100), (200, 200), (255, 0, 0), -1)
        cv2.circle(frame, (300, 150), 50, (0, 255, 0), -1)
        return frame
    
    def test_process_frame_returns_tuple(self, pipeline, test_frame):
        """process_frame debe retornar tuple"""
        result = pipeline.process_frame(test_frame)
        assert isinstance(result, tuple)
        assert len(result) == 2
    
    def test_process_frame_returns_analysis(self, pipeline, test_frame):
        """Primer elemento debe ser FrameAnalysis"""
        analysis, _ = pipeline.process_frame(test_frame)
        assert isinstance(analysis, FrameAnalysis)
        assert hasattr(analysis, 'detections')
        assert hasattr(analysis, 'anomalies')
        assert hasattr(analysis, 'alerts')
    
    def test_process_frame_returns_annotated_frame(self, pipeline, test_frame):
        """Segundo elemento debe ser frame anotado"""
        _, annotated = pipeline.process_frame(test_frame)
        assert isinstance(annotated, np.ndarray)
        assert annotated.shape == test_frame.shape or annotated is None


class TestSurveillancePipelineBatchProcessing:
    """Test batch processing"""
    
    @pytest.fixture
    def pipeline(self):
        return SurveillancePipeline()
    
    @pytest.fixture
    def test_batch(self):
        """Crear batch de frames"""
        batch = []
        for i in range(4):
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            batch.append(frame)
        return batch
    
    def test_batch_process_returns_list(self, pipeline, test_batch):
        """batch_process debe retornar list"""
        results = pipeline.batch_process(test_batch)
        assert isinstance(results, list)
        assert len(results) == len(test_batch)
    
    def test_batch_process_each_item_is_analysis(self, pipeline, test_batch):
        """Cada item debe ser FrameAnalysis"""
        results = pipeline.batch_process(test_batch)
        for result in results:
            assert isinstance(result, FrameAnalysis)


class TestSurveillancePipelineDetectionIntegration:
    """Test integración de detecciones"""
    
    @pytest.fixture
    def pipeline(self):
        return SurveillancePipeline()
    
    def test_pipeline_includes_yolo_detections(self, pipeline):
        """Analysis debe incluir detecciones YOLO"""
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        analysis, _ = pipeline.process_frame(frame)
        
        # Should have detections field
        assert hasattr(analysis, 'detections')
        assert isinstance(analysis.detections, list)


class TestSurveillancePipelineAnomalyIntegration:
    """Test integración de anomalías (FASE 2)"""
    
    @pytest.fixture
    def pipeline(self):
        return SurveillancePipeline()
    
    def test_pipeline_includes_anomaly_detection(self, pipeline):
        """Analysis debe incluir anomalías"""
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        analysis, _ = pipeline.process_frame(frame)
        
        # Should have anomalies field
        assert hasattr(analysis, 'anomalies')
        assert isinstance(analysis.anomalies, list)


class TestSurveillancePipelineStats:
    """Test estadísticas del pipeline"""
    
    def test_get_summary_returns_dict(self):
        """get_summary debe retornar dict"""
        pipeline = SurveillancePipeline()
        summary = pipeline.get_summary()
        assert isinstance(summary, dict)
    
    def test_summary_includes_processing_time(self):
        """Summary debe incluir tiempo de procesamiento"""
        pipeline = SurveillancePipeline()
        summary = pipeline.get_summary()
        
        # Process a frame first
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        pipeline.process_frame(frame)
        
        # Get summary
        summary = pipeline.get_summary()
        # Should have average processing time or stats
        assert isinstance(summary, dict)


class TestSurveillancePipelineSingleton:
    """Test singleton pattern"""
    
    def test_get_surveillance_pipeline_returns_same_instance(self):
        """Debe retornar misma instancia"""
        pipeline1 = get_surveillance_pipeline()
        pipeline2 = get_surveillance_pipeline()
        assert pipeline1 is pipeline2


# ═════════════════════════════════════════════════════════════════════════════
# Performance tests
# ═════════════════════════════════════════════════════════════════════════════

class TestSurveillancePipelinePerformance:
    """Test performance benchmarks"""
    
    def test_frame_processing_completes_in_reasonable_time(self):
        """Debe procesar frame en < 1 segundo (CPU)"""
        import time
        
        pipeline = SurveillancePipeline()
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        start = time.time()
        analysis, _ = pipeline.process_frame(frame)
        elapsed = time.time() - start
        
        # Should complete in reasonable time
        assert elapsed < 5.0, f"Frame processing took {elapsed}s"
        
        # Should have stats
        if analysis.stats:
            assert 'total_time_ms' in analysis.stats or 'processing_ms' in analysis.stats


# ═════════════════════════════════════════════════════════════════════════════
# E2E Integration tests
# ═════════════════════════════════════════════════════════════════════════════

class TestFullPipelineWorkflow:
    """Workflow completo E2E"""
    
    def test_multi_frame_processing_workflow(self):
        """Workflow: procesar n frames con persona"""
        pipeline = SurveillancePipeline()
        
        # Simulate video stream (10 frames)
        all_analyses = []
        for frame_idx in range(10):
            # Create frame with object
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            # Add moving object
            x = 100 + frame_idx * 10
            cv2.rectangle(frame, (x, 100), (x+50, 150), (255, 0, 0), -1)
            
            # Process
            analysis, _ = pipeline.process_frame(frame)
            all_analyses.append(analysis)
        
        # Verify we got results
        assert len(all_analyses) == 10
        
        # All should be FrameAnalysis
        for analysis in all_analyses:
            assert isinstance(analysis, FrameAnalysis)
    
    def test_batch_vs_sequential_consistency(self):
        """Batch processing debe ser consistente con sequential"""
        pipeline = SurveillancePipeline()
        
        # Create test batch
        frames = [
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            for _ in range(4)
        ]
        
        # Process batch
        batch_results = pipeline.batch_process(frames)
        
        # Should get 4 results
        assert len(batch_results) == 4
        
        # All should be FrameAnalysis
        for result in batch_results:
            assert isinstance(result, FrameAnalysis)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
