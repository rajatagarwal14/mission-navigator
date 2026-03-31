#!/bin/bash
set -e

echo "=== Building Mission Navigator ==="

# Build frontend
echo "[1/5] Building frontend..."
cd frontend
npm install
npm run build
cd ..

# Install backend dependencies
echo "[2/5] Installing backend dependencies..."
pip install -r backend/requirements.txt

# Initialize database
echo "[3/5] Initializing database..."
cd backend
python3 -c "
import asyncio, sys
sys.path.insert(0, '.')
from database import init_db
asyncio.run(init_db())
print('Database initialized')
"

# Seed admin
echo "[4/5] Seeding admin user..."
python3 scripts/seed_admin.py 2>/dev/null || echo "Admin exists"

# Ingest knowledge base during build
echo "[5/5] Ingesting knowledge base..."
python3 scripts/ingest_bridge_guide.py || echo "Ingestion skipped (may need API key)"

echo "=== Build complete ==="
