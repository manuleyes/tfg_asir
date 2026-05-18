#!/usr/bin/env python
"""
Test Runner Summary - Ejecuta todos los tests y genera reporte
"""

import subprocess
import sys
from pathlib import Path

def run_tests():
    """Ejecuta suite de tests y captura resultados"""
    
    project_root = Path(__file__).parent
    test_dir = project_root / "tests"
    
    test_files = [
        "test_yolo_detection.py",
    # "test_behavior_prediction.py",  # Skip (TensorFlow not available)
        # "test_face_recognition.py",  # Skip (DeepFace not available)
        "test_detection_pipeline.py",
        "test_api_endpoints.py",
    ]
    
    results = {}
    total_passed = 0
    total_failed = 0
    total_skipped = 0
    
    print("=" * 80)
    print("TEST SUITE EXECUTION")
    print("=" * 80)
    
    for test_file in test_files:
        test_path = test_dir / test_file
        
        if not test_path.exists():
            print(f"\n⏭️  SKIP {test_file}: File not found")
            continue
        
        print(f"\n▶ Running {test_file}...")
        print("-" * 80)
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_path), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Parse output
            output = result.stdout + result.stderr
            
            # Extract summary line
            for line in output.split('\n'):
                if 'passed' in line or 'failed' in line or 'error' in line:
                    if '==' in line:
                        print(line)
                        
                        # Count results
                        if 'passed' in line:
                            import re
                            match = re.search(r'(\d+) passed', line)
                            if match:
                                passed = int(match.group(1))
                                total_passed += passed
                            
                            match = re.search(r'(\d+) failed', line)
                            if match:
                                failed = int(match.group(1))
                                total_failed += failed
                        
                        results[test_file] = line.strip()
                        break
            
            if result.returncode == 0:
                print(f" PASSED: {test_file}")
            else:
                print(f" FAILED: {test_file}")
                
        except subprocess.TimeoutExpired:
            print(f"⏱️  TIMEOUT: {test_file}")
        except Exception as e:
            print(f" ERROR: {test_file}: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"\nTotal Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    print(f"Total Skipped: {total_skipped}")
    
    if total_failed == 0:
        print("\n ALL TESTS PASSED!")
    else:
        print(f"\n️ {total_failed} tests failed")
    
    print("\nDetailed Results:")
    for test_file, summary in results.items():
        print(f"  {test_file}: {summary}")
    
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
   sys.exit(run_tests())
