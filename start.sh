#!/bin/bash
# Mission Navigator - Quick Start Script
set -e

echo "==================================="
echo "  Mission Navigator - Quick Start  "
echo "==================================="

# Check for .env
if [ ! -f backend/.env ]; then
    echo "Creating .env from template..."
    cp .env.example backend/.env
    echo "IMPORTANT: Add your GEMINI_API_KEY to backend/.env"
fi

# Install backend dependencies
echo ""
echo "[1/5] Installing backend dependencies..."
cd backend
pip install -r requirements.txt -q

# Initialize database
echo "[2/5] Initializing database..."
python3 -c "
import asyncio, sys
sys.path.insert(0, '.')
from database import init_db
asyncio.run(init_db())
print('Database initialized')
"

# Seed admin user
echo "[3/5] Seeding admin user..."
python3 scripts/seed_admin.py 2>/dev/null || true

# Ingest knowledge base (requires GEMINI_API_KEY)
echo "[4/5] Checking knowledge base..."
python3 -c "
from config import settings
if settings.GEMINI_API_KEY:
    print('API key found - run: cd backend && python3 scripts/ingest_bridge_guide.py')
else:
    print('WARNING: No GEMINI_API_KEY set. Add it to backend/.env then run:')
    print('  cd backend && python3 scripts/ingest_bridge_guide.py')
"

# Start servers
echo "[5/5] Starting servers..."
echo ""
echo "Backend: http://localhost:8000 (API docs: http://localhost:8000/docs)"
echo "Frontend: http://localhost:5173"
echo "Admin Dashboard: http://localhost:5173/admin/login (admin/admin123)"
echo ""

cd ..

# Start both servers
(cd backend && python3 -m uvicorn main:app --reload --port 8000) &
BACKEND_PID=$!

(cd frontend && npm run dev) &
FRONTEND_PID=$!

echo "Servers starting... Press Ctrl+C to stop both."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
