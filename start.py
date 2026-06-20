#!/usr/bin/env python3
"""
Padyarchana Application Entry Point

This script can be run directly with: python start.py
"""
import sys
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("  పద్యార్చన (Padyarchana) - Starting Application")
    print("=" * 60)
    print()
    print("🚀 Starting Padyarchana web server...")
    print("📍 Application: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8080,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Goodbye!")
        sys.exit(0)
