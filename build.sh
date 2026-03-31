#!/bin/bash
# Build script for Render deployment
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

# Initialize database
echo "[3/4] Initializing database..."
cd backend
python3 -c "
import asyncio, sys
sys.path.insert(0, '.')
from database import init_db
asyncio.run(init_db())
print('Database initialized')
"

# Seed admin user
echo "[4/4] Seeding admin user..."
python3 scripts/seed_admin.py 2>/dev/null || echo "Admin already exists"

# Ingest knowledge base if not already done
python3 -c "
from services.knowledge_service import knowledge_service
count = knowledge_service.get_collection_count()
if count == 0:
    print('Knowledge base empty - running ingestion...')
    import subprocess
    subprocess.run(['python3', 'scripts/ingest_bridge_guide.py'], check=True)
else:
    print(f'Knowledge base already has {count} chunks - skipping ingestion')
"

echo "=== Build complete ==="
