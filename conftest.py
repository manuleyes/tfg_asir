"""
conftest.py — pytest path setup for project root execution.
Adds backend/ to sys.path so that imports inside backend/app.py
(e.g. from routes import ...) resolve correctly when tests are run
from the project root directory.
"""
import sys
import os

# Allow "from routes import ..." inside backend/app.py
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
