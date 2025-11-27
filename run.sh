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

# Check for Tesseract OCR (optional - for Nethra feature)
if command -v tesseract &> /dev/null; then
    echo "✓ Tesseract OCR found"
    if tesseract --list-langs 2>&1 | grep -q "tel"; then
        echo "✓ Telugu language pack available"
    else
        echo "⚠ Telugu language pack not found. For OCR features, run: sudo apt-get install tesseract-ocr-tel"
    fi
else
    echo "⚠ Tesseract OCR not installed. For OCR features, run: sudo apt-get install tesseract-ocr tesseract-ocr-tel"
fi

# Check if database exists
if [ ! -f "padyarchana.db" ]; then
    echo "⚠ Database not found. Creating database..."
    python scripts/seed_data.py
    echo ""
fi

echo ""
echo "🚀 Starting Padyarchana web server..."
echo "📍 Application will be available at: http://localhost:8000"
echo "📚 API documentation at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo "============================================================"
echo ""

# Start the application using uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
