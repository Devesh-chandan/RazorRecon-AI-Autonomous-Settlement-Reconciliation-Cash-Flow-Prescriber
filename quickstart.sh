#!/usr/bin/env bash
# Quickstart script for hackathon judges & evaluators

set -e

echo "========================================================"
echo "⚡ RazorRecon — Automated Judge Quickstart"
echo "========================================================"

echo "[1/4] Starting Docker infrastructure (PostgreSQL 16 + Redis 7)..."
docker compose up -d

echo "[2/4] Running database migrations..."
cd backend
python -m alembic upgrade head

echo "[3/4] Seeding benchmark 100-record dataset..."
python -m app.seed
cd ..

echo "[4/4] Running Pytest unit test suite..."
PYTHONPATH=backend pytest tests/ -v

echo ""
echo "========================================================"
echo "✅ RazorRecon is ready!"
echo "Backend URL:  http://localhost:8000"
echo "Swagger Docs: http://localhost:8000/docs"
echo "Frontend UI:  http://localhost:5173"
echo "========================================================"
