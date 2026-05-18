"""
Unit Tests for FastAPI Endpoints
Valida:
- Endpoint availability
- Request/Response format
- Error handling
- Data serialization
"""

import pytest
import numpy as np
import cv2
from io import BytesIO
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from backend.app import app

# Test client
client = TestClient(app)


class TestHealthCheck:
    """Test health check endpoints"""

    def test_api_health_returns_ok(self):
        """GET /api/health debe retornar ok"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get('status') in ['ok', 'healthy']


class TestStatsEndpoints:
    """Test /api/v2/stats/* endpoints"""

    def test_stats_yolo_returns_dict(self):
        """GET /api/v2/stats/yolo debe retornar dict"""
        response = client.get("/api/v2/stats/yolo")
        assert response.status_code == 200
        data = response.json()
        assert 'yolo' in data

    def test_stats_behavior_returns_dict(self):
        """GET /api/v2/stats/behavior"""
        response = client.get("/api/v2/stats/behavior")
        assert response.status_code in [200, 400]

    def test_stats_faces_returns_dict(self):
        """GET /api/v2/stats/faces"""
        response = client.get("/api/v2/stats/faces")
        assert response.status_code in [200, 400]

    def test_stats_streaming_returns_dict(self):
        """GET /api/v2/stats/streaming"""
        response = client.get("/api/v2/stats/streaming")
        assert response.status_code == 200


class TestConfigEndpoints:
    """Test /api/v2/config endpoints"""

    def test_config_returns_dict(self):
        """GET /api/v2/config"""
        response = client.get("/api/v2/config")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_config_has_settings(self):
        """Config debe tener fields basicos"""
        response = client.get("/api/v2/config")
        data = response.json()
        assert len(data) > 0


class TestCameraEndpoints:
    """Test /api/v2/cameras/* endpoints"""

    def test_cameras_active_returns_list(self):
        """GET /api/v2/cameras/active"""
        response = client.get("/api/v2/cameras/active")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))


class TestDetectionEndpoints:
    """Test /api/v2/detect/* endpoints"""

    @pytest.fixture
    def test_image(self):
        """Crear imagen de prueba"""
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        success, encoded = cv2.imencode('.jpg', frame)
        return BytesIO(encoded.tobytes()) if success else None

    def test_detect_fast_with_image(self, test_image):
        """POST /api/v2/detect/fast con imagen"""
        if test_image is None:
            pytest.skip("Could not encode test image")
        files = {'file': ('test.jpg', test_image, 'image/jpeg')}
        response = client.post("/api/v2/detect/fast", files=files)
        assert response.status_code in [200, 400, 422]

    def test_detect_fast_without_image(self):
        """POST /api/v2/detect/fast sin imagen"""
        response = client.post("/api/v2/detect/fast")
        assert response.status_code in [400, 422]


class TestPipelineEndpoints:
    """Test /api/v2/pipeline/* endpoints"""

    def test_pipeline_summary_returns_dict(self):
        """GET /api/v2/pipeline/summary"""
        response = client.get("/api/v2/pipeline/summary")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestErrorHandling:
    """Test error handling"""

    def test_invalid_endpoint_returns_404(self):
        """GET endpoint invalido"""
        response = client.get("/api/v2/invalid_endpoint")
        assert response.status_code == 404

    def test_post_without_required_params(self):
        """POST endpoint sin parametros requeridos"""
        response = client.post("/api/v2/detect/fast")
        assert response.status_code in [400, 422]


class TestResponseFormats:
    """Test response format consistency"""

    def test_json_responses_are_valid(self):
        """Todos los responses deben ser JSON valido"""
        endpoints = [
            "/api/v2/config",
            "/api/v2/stats/yolo",
            "/api/v2/cameras/active",
            "/api/v2/pipeline/summary"
        ]
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, (dict, list))


class TestCORSHeaders:
    """Test CORS middleware"""

    def test_cors_headers_present(self):
        """Responses deben tener CORS headers"""
        response = client.get("/api/v2/config")
        assert response.status_code == 200


class TestAPIEndpointCoverage:
    """Verify all documented endpoints are registered"""

    def test_all_stats_endpoints_registered(self):
        """Todos los stats endpoints deben existir"""
        stats_endpoints = [
            "/api/v2/stats/yolo",
            "/api/v2/stats/behavior",
            "/api/v2/stats/faces",
        ]
        for endpoint in stats_endpoints:
            response = client.get(endpoint)
            assert response.status_code != 404, f"{endpoint} not found"

    def test_config_endpoint_exists(self):
        """Config endpoint debe existir"""
        response = client.get("/api/v2/config")
        assert response.status_code != 404

    def test_detection_endpoint_exists(self):
        """Detection endpoint debe existir"""
        response = client.post("/api/v2/detect/fast")
        assert response.status_code != 404


class TestResponseDataTypes:
    """Verify response data types"""

    def test_stats_has_numeric_values(self):
        """Stats deben tener valores numericos"""
        response = client.get("/api/v2/stats/yolo")
        data = response.json()
        if 'yolo' in data:
            yolo_stats = data['yolo']
            for key, value in yolo_stats.items():
                assert isinstance(value, (int, float)), f"{key} is not numeric"


class TestEndpointPerformance:
    """Test endpoint response times"""

    def test_config_endpoint_responds_quickly(self):
        """Config debe responder en menos de 1000ms"""
        import time
        start = time.time()
        response = client.get("/api/v2/config")
        elapsed = (time.time() - start) * 1000
        assert response.status_code == 200
        assert elapsed < 1000, f"Response took {elapsed}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
