#!/bin/bash

# Padyarchana Application Startup Script

echo "============================================================"
echo "  పద్యార్చన (Padyarchana) - Starting Application"
echo "============================================================"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "✓ Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠ Virtual environment not found. Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if database exists
if [ ! -f "padyarchana.db" ]; then
    echo "⚠ Database not found. Creating database..."
    python scripts/seed_data.py
    echo ""
fi

echo "🚀 Starting Padyarchana web server..."
echo "📍 Application will be available at: http://localhost:8000"
echo "📚 API documentation at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo "============================================================"
echo ""

# Start the application using uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
