"""
Test Suite Package for Vigilancia Inteligente
"""

__version__ = "1.0.0"
__author__ = "GitHub Copilot"

# Make test utilities available
from typing import Any

def load_test_fixtures() -> dict:
    """Load common test fixtures"""
    return {
        'test_frame_shape': (480, 640, 3),
        'test_image_formats': ['jpg', 'png', 'bmp'],
        'test_batch_sizes': [1, 4, 8, 16],
    }
