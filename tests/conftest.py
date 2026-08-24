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

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Ensure all database tables are created before running tests."""
    from app.database import engine, Base
    import app.models  # noqa: F401 Ensure all models are registered with Base.metadata

    Base.metadata.create_all(bind=engine)
    yield


