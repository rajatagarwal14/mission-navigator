#!/bin/bash
set -e

echo "=== Building Mission Navigator ==="

# Build frontend
echo "[1/4] Building frontend..."
cd frontend
npm install
npm run build
cd ..

# Install backend dependencies
echo "[2/4] Installing backend dependencies..."
pip install -r backend/requirements.txt

# Initialize database and seed admin
echo "[3/4] Initializing database..."
cd backend
python3 -c "
import asyncio, sys
sys.path.insert(0, '.')
from database import init_db
asyncio.run(init_db())
print('Database initialized')
"
python3 scripts/seed_admin.py 2>/dev/null || echo "Admin exists"

# Ingest knowledge base if empty
echo "[4/4] Checking knowledge base..."
python3 -c "
import sys
sys.path.insert(0, '.')
from services.knowledge_service import knowledge_service
count = knowledge_service.get_collection_count()
if count == 0:
    print('Knowledge base empty - will ingest on first start')
else:
    print(f'Knowledge base has {count} chunks')
"

echo "=== Build complete ==="
