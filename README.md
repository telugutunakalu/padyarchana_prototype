# పద్యార్చన (Padyarchana)

**Advanced Search and Analysis Engine for Telugu Poetry**

## Overview

Padyarchana is a comprehensive web-based platform for searching, analyzing, and exploring Telugu poetry (Padyalu). It provides rich metadata, advanced search capabilities, and powerful analytical tools for students, researchers, linguists, and enthusiasts of Telugu literature.

## Features

### Core Features
- **Centralized Database**: Large collection of Telugu poems spanning different eras and poets
- **Rich Metadata**: Comprehensive tagging including poet, era, meter (Chandassu), Sandhi, Samasa, Gana, Yati, and Prasa
- **Advanced Search**: Query poems by text, poet, era, meter, and various prosodic/grammatical features
- **Hyperlinked Poem View**: Interactive poem display with clickable words for definitions and analysis
- **Comparative Analysis**: Tools to compare poems and poets based on style and structure
- **Telugu Dictionary Integration**: Instant word definitions and grammatical analysis

### Aksharanusarika (అక్షరానుసారిక)
- **Prosodic Analysis**: Analyze poems for Guru-Laghu patterns, Gana structure, and metrical composition
- **Interactive Visualization**: Dynamic charts and tables showing syllable analysis
- **Meter Detection**: Identify and validate traditional Telugu meters (Chandassu)

### Laya (లయ) - Audio Annotation
- **Audio Upload**: Upload audio recordings of poem recitations
- **Syllable-Level Annotation**: Map audio timestamps to text syllables
- **Playback Controls**: Synchronized audio playback with text highlighting

### Nethra (నేత్ర) - OCR Annotation Portal
- **Image OCR**: Extract Telugu text from scanned poem images using Tesseract
- **Batch Processing**: Organize images by folder/batch for systematic annotation
- **Multi-Label Support**: Tag images with multiple labels (correct, incorrect, needs review, unreadable)
- **Annotation Workflow**: Side-by-side view of image and extracted/corrected text

### TTS Integration
- **Text-to-Speech**: Generate audio for poems using Indic TTS
- **Batch Generation**: Queue-based TTS generation for multiple poems

## Technology Stack

- **Backend**: FastAPI, SQLAlchemy, Python 3.11+
- **Database**: SQLite with async support (aiosqlite)
- **Frontend**: Jinja2 Templates, Alpine.js, CSS
- **NLP**: indic-nlp-library, custom Telugu processing
- **OCR**: Tesseract OCR with Telugu language pack

## Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Tesseract OCR (optional, for Nethra feature)

### Quick Setup

```bash
# Clone repository
git clone <repository-url>
cd padyarchana_prototype

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# (Optional) Install Tesseract for OCR features
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-tel

# Create environment file
cp .env.example .env

# Initialize database with seed data
python scripts/seed_data.py
```

### System Dependencies

#### For OCR (Nethra) Feature
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-tel

# macOS
brew install tesseract tesseract-lang

# Verify installation
tesseract --list-langs  # Should show 'tel'
```

## Running the Application

### Using the startup script (recommended)
```bash
./run.sh
```

### Manual startup
```bash
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The application will be available at:
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
padyarchana_prototype/
├── app/
│   ├── api/                 # API route handlers
│   │   ├── poems.py         # Poem CRUD endpoints
│   │   ├── poets.py         # Poet endpoints
│   │   ├── meters.py        # Meter endpoints
│   │   ├── search.py        # Search functionality
│   │   ├── dictionary.py    # Dictionary lookups
│   │   ├── compare.py       # Comparative analysis
│   │   ├── audio.py         # Audio upload/management
│   │   ├── tts.py           # Text-to-speech endpoints
│   │   └── nethra.py        # OCR annotation endpoints
│   ├── models/              # SQLAlchemy database models
│   ├── schemas/             # Pydantic validation schemas
│   ├── services/            # Business logic
│   │   └── ocr_service.py   # Tesseract OCR wrapper
│   ├── templates/           # Jinja2 HTML templates
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection
│   └── main.py              # FastAPI application entry point
├── static/                  # Static files (CSS, JS, fonts, audio)
├── aksharanusarika/         # Prosodic analysis module
├── nethra/                  # OCR images folder (organized by batch)
├── scripts/                 # Utility scripts
│   └── seed_data.py         # Database seeding script
├── padyalu_json_data/       # Seed data (JSON files)
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── run.sh                   # Application startup script
└── README.md                # This file
```

## Web Routes

| Route | Description |
|-------|-------------|
| `/` | Homepage |
| `/search` | Search poems |
| `/poem/{id}` | Poem detail page |
| `/poet/{id}` | Poet detail with poems |
| `/meter/{id}` | Meter detail with poems |
| `/poets` | Browse all poets |
| `/meters` | Browse all meters |
| `/aksharanusarika` | Prosodic analysis tool |
| `/laya/{poem_id}` | Audio annotation tool |
| `/nethra` | OCR annotation dashboard |
| `/nethra/batch/{id}` | OCR annotation interface |
| `/admin/tts` | TTS administration |

## API Endpoints

### Poems
- `GET /api/poems` - List all poems
- `GET /api/poems/{id}` - Get poem details
- `POST /api/poems` - Create new poem
- `PUT /api/poems/{id}` - Update poem
- `DELETE /api/poems/{id}` - Delete poem

### Poets
- `GET /api/poets` - List all poets
- `GET /api/poets/{id}` - Get poet details

### Meters
- `GET /api/meters` - List all meters
- `GET /api/meters/{id}` - Get meter details

### Search
- `GET /api/search` - Search poems with filters
- `GET /api/search/autocomplete` - Get search suggestions

### Dictionary
- `GET /api/dictionary/{word}` - Get word definition

### Comparative Analysis
- `GET /api/compare/poems` - Compare multiple poems
- `GET /api/compare/poets` - Compare multiple poets

### Audio
- `POST /api/poems/{id}/audio` - Upload audio for poem
- `GET /api/poems/{id}/audio` - Get poem audio

### Nethra OCR
- `GET /api/nethra/batches` - List image batches
- `POST /api/nethra/batches/scan` - Scan for new images
- `GET /api/nethra/batches/{id}/images` - Get images in batch
- `POST /api/nethra/images/{id}/ocr` - Run OCR on image
- `PUT /api/nethra/images/{id}` - Save annotation
- `GET /api/nethra/stats` - Get annotation statistics

### TTS
- `POST /api/tts/generate/{poem_id}` - Generate TTS audio

## Seed Data

The project includes seed data from multiple Telugu poets:
- **Vemana** (వేమన) - Vemana Satakam
- **Sumathi Satakam** (సుమతీ శతకము)
- **Abhinava Sumathi Satakam** (అభినవ సుమతీ శతకము)

To load/reload seed data:
```bash
python scripts/seed_data.py
```

## Development

### Running Tests
```bash
pytest
```

With coverage:
```bash
pytest --cov=app --cov-report=html
```

### Code Formatting
```bash
black app/ tests/
```

### Linting
```bash
flake8 app/ tests/
```

## Configuration

Environment variables (`.env` file):

```env
APP_NAME=Padyarchana
DEBUG=true
HOST=0.0.0.0
PORT=8000
DATABASE_URL=sqlite+aiosqlite:///./padyarchana.db
```

## Troubleshooting

### OCR not working
1. Verify Tesseract is installed: `tesseract --version`
2. Check Telugu language pack: `tesseract --list-langs | grep tel`
3. Install if missing: `sudo apt-get install tesseract-ocr tesseract-ocr-tel`

### Database issues
1. Delete `padyarchana.db` and re-run seed script
2. Check file permissions

### Import errors
1. Ensure virtual environment is activated
2. Re-install dependencies: `pip install -r requirements.txt`

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

Open Source - See LICENSE file for details

---

**పద్యార్చన** - Preserving and celebrating Telugu literary heritage through technology.
