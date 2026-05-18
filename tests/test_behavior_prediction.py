"""
Behavior Prediction module removed (requires TensorFlow/LSTM).
All tests skipped.
"""
import pytest

pytestmark = pytest.mark.skip(reason="Behavior predictor module removed")



class TestTrajectoryPoint:
    """Test dataclass TrajectoryPoint"""
    
    def test_trajectory_point_creation(self):
        """Debe crear punto de trayectoria"""
        point = TrajectoryPoint(x=100.0, y=200.0, timestamp=0.5, confidence=0.95)
        assert point.x == 100.0
        assert point.y == 200.0
        assert point.timestamp == 0.5
        assert point.confidence == 0.95
    
    def test_trajectory_point_distance(self):
        """Debe calcular distancia euclidiana"""
        point1 = TrajectoryPoint(x=0.0, y=0.0, timestamp=0)
        point2 = TrajectoryPoint(x=3.0, y=4.0, timestamp=0.1)
        
        distance = point1.distance_to(point2)
        expected = 5.0  # 3-4-5 triangle
        assert abs(distance - expected) < 0.01


class TestBehaviorPredictorInitialization:
    """Test inicialización del predictor"""
    
    def test_behavior_predictor_creates(self):
        """Debe crear instancia"""
        predictor = BehaviorPredictor(sequence_length=30, anomaly_threshold=0.7)
        assert predictor is not None
        assert predictor.sequence_length == 30
        assert predictor.anomaly_threshold == 0.7
    
    def test_behavior_predictor_has_empty_stats(self):
        """Stats debe iniciar vacío"""
        predictor = BehaviorPredictor()
        assert predictor.stats['total_persons'] == 0
        assert predictor.stats['anomalies_detected'] == 0


class TestBehaviorPredictorTrajectories:
    """Test tracking de trayectorias"""
    
    @pytest.fixture
    def predictor(self):
        return BehaviorPredictor(sequence_length=5)
    
    def test_add_detection_creates_trajectory(self, predictor):
        """Debe crear trayectoria para nueva persona"""
        detection = {
            'x': 100,
            'y': 200,
            'confidence': 0.9
        }
        predictor.add_detection('p1', detection)
        assert 'p1' in predictor.trajectories
    
    def test_trajectory_grows_with_detections(self, predictor):
        """Trayectoria debe crecer con detecciones"""
        person_id = 'p1'
        
        for i in range(5):
            detection = {
                'x': 100 + i * 10,
                'y': 200 + i * 5,
                'confidence': 0.9
            }
            predictor.add_detection(person_id, detection)
        
        trajectory = predictor.trajectories[person_id]
        assert len(trajectory) == 5
    
    def test_trajectory_maintains_max_length(self, predictor):
        """Trayectoria no debe exceder sequence_length"""
        person_id = 'p1'
        max_len = predictor.sequence_length
        
        # Add more than max
        for i in range(max_len + 10):
            detection = {
                'person_id': person_id,
                'x': 100 + i,
                'y': 200 + i,
                'confidence': 0.9
            }
            predictor.add_detection(detection, timestamp=i * 0.033)
        
        trajectory = predictor.trajectories[person_id]
        assert len(trajectory) <= max_len


class TestBehaviorPredictorAnomalyDetection:
    """Test detección de anomalías"""
    
    @pytest.fixture
    def predictor(self):
        return BehaviorPredictor(sequence_length=10, anomaly_threshold=0.5)
    
    def test_detect_anomaly_returns_float(self, predictor):
        """detect_anomaly debe retornar float"""
        detection = {'person_id': 'p1', 'x': 100, 'y': 200, 'confidence': 0.9}
        predictor.add_detection(detection, timestamp=0.0)
        
        score = predictor.detect_anomaly('p1')
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
    
    def test_detect_anomaly_consistent_movement(self, predictor):
        """Movimiento consistente debe tener baja anomalía"""
        person_id = 'p1'
        
        # Add linear trajectory
        for i in range(20):
            detection = {
                'person_id': person_id,
                'x': 100 + i * 10,
                'y': 200 + i * 5,
                'confidence': 0.9
            }
            predictor.add_detection(detection, timestamp=i * 0.033)
        
        anomaly_score = predictor.detect_anomaly(person_id)
        # Linear movement should be low anomaly
        assert anomaly_score is not None


class TestZoneMonitoring:
    """Test monitoreo de zones"""
    
    @pytest.fixture
    def monitor(self):
        # Square zone: (100, 100) -> (200, 200)
        polygon = [[100, 100], [200, 100], [200, 200], [100, 200]]
        return ZoneMonitor('test_zone', polygon, zone_type='restricted')
    
    def test_zone_monitor_creation(self, monitor):
        """Debe crear zone monitor"""
        assert monitor.zone_name == 'test_zone'
        assert monitor.zone_type == 'restricted'
    
    def test_point_in_zone_inside(self, monitor):
        """Punto dentro debe detectarse"""
        is_inside = monitor.is_point_in_zone(150, 150)
        assert is_inside == True
    
    def test_point_in_zone_outside(self, monitor):
        """Punto afuera debe detectarse"""
        is_inside = monitor.is_point_in_zone(50, 50)
        assert is_inside == False
    
    def test_point_in_zone_boundary(self, monitor):
        """Punto en borde"""
        # Edge case - point on boundary
        is_inside = monitor.is_point_in_zone(100, 100)
        # Ray-casting may or may not include boundary
        assert isinstance(is_inside, bool)


class TestBehaviorPredictorSingleton:
    """Test singleton pattern"""
    
    def test_get_behavior_predictor_returns_same_instance(self):
        """Debe retornar misma instancia"""
        predictor1 = get_behavior_predictor()
        predictor2 = get_behavior_predictor()
        assert predictor1 is predictor2


class TestBehaviorPredictorStats:
    """Test estadísticas"""
    
    def test_stats_updates_total_persons(self):
        """Stats debe trackear personas"""
        predictor = BehaviorPredictor()
        
        # Add detections for 3 different people
        for person_id in ['p1', 'p2', 'p3']:
            detection = {
                'person_id': person_id,
                'x': 100,
                'y': 200,
                'confidence': 0.9
            }
            predictor.add_detection(detection)
        
        assert predictor.stats['total_persons'] == 3


# ═════════════════════════════════════════════════════════════════════════════
# Integration-style tests
# ═════════════════════════════════════════════════════════════════════════════

class TestBehaviorPredictorEndToEnd:
    """E2E behavior prediction test"""
    
    def test_full_workflow(self):
        """Workflow completo: add -> detect -> check"""
        predictor = BehaviorPredictor(sequence_length=5)
        
        # Create zone
        zone = ZoneMonitor(
            'test',
            [[0, 0], [500, 0], [500, 500], [0, 500]],
            'monitoring'
        )
        
        # Simulate person crossing zone
        timestamps = np.linspace(0, 1.0, 10)
        for i, t in enumerate(timestamps):
            # Person moves from left to right
            x = 50 + i * 40
            y = 250
            
            detection = {
                'person_id': 'p1',
                'x': x,
                'y': y,
                'confidence': 0.95
            }
            predictor.add_detection(detection, timestamp=t)
            
            # Check zone
            in_zone = zone.is_point_in_zone(x, y)
            if x > 0 and x < 500:
                assert in_zone == True
        
        # Verify trajectory was recorded
        assert 'p1' in predictor.trajectories
        assert len(predictor.trajectories['p1']) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
