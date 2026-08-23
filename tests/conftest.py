"""Pytest configuration and IDE path resolver.

Ensures the `backend/` directory is in `sys.path` so IDE linters (Pylance, Pyright, etc.)
and test runners resolve `import app` cleanly without configuration issues.
"""
import sys
from pathlib import Path

# Add backend directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
