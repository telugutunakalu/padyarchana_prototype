# పద్యార్చన (Padyarchana)

**Advanced Search and Analysis Engine for Telugu Poetry**

## Overview

Padyarchana is a comprehensive web-based platform for searching, analyzing, and exploring Telugu poetry (Padyalu). It provides rich metadata, advanced search capabilities, and powerful analytical tools for students, researchers, linguists, and enthusiasts of Telugu literature.

## Features

- **Centralized Database**: Large collection of Telugu poems spanning different eras and poets
- **Rich Metadata**: Comprehensive tagging including poet, era, meter (Chandassu), Sandhi, Samasa, Gana, Yati, and Prasa
- **Advanced Search**: Query poems by text, poet, era, meter, and various prosodic/grammatical features
- **Hyperlinked Poem View**: Interactive poem display with clickable words for definitions and analysis
- **Comparative Analysis**: Tools to compare poems and poets based on style and structure
- **Pattern Recognition**: Identify recurring patterns in word usage, Gana sequences, and structural elements
- **Telugu Dictionary Integration**: Instant word definitions and grammatical analysis

## Technology Stack

- **Backend**: FastAPI, SQLAlchemy, Python 3.11+
- **Database**: SQLite with FTS5 (Full-Text Search)
- **Frontend**: Jinja2 Templates, Alpine.js, Tailwind CSS
- **NLP**: indic-nlp-library, custom Telugu processing

## Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Setup

1. Clone the repository or extract the project files

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

5. Initialize the database and load seed data:
```bash
python scripts/seed_data.py
```

## Running the Application

### Development Mode

```bash
python app/main.py
```

Or using uvicorn directly:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at:
- Web Interface: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Alternative API Docs: http://localhost:8000/redoc

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Project Structure

```
padyarchana/
├── app/
│   ├── api/                 # API route handlers
│   ├── models/              # SQLAlchemy database models
│   ├── schemas/             # Pydantic validation schemas
│   ├── services/            # Business logic
│   ├── utils/               # Utility functions
│   ├── templates/           # Jinja2 HTML templates
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection
│   └── main.py              # FastAPI application entry point
├── static/                  # Static files (CSS, JS, fonts)
├── tests/                   # Test files
├── data/                    # Data files
├── padyalu_json_data/       # Seed data (JSON files)
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
└── README.md                # This file
```

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
- `POST /api/poets` - Create new poet
- `PUT /api/poets/{id}` - Update poet
- `DELETE /api/poets/{id}` - Delete poet

### Meters
- `GET /api/meters` - List all meters
- `GET /api/meters/{id}` - Get meter details
- `POST /api/meters` - Create new meter
- `PUT /api/meters/{id}` - Update meter
- `DELETE /api/meters/{id}` - Delete meter

### Search
- `GET /api/search` - Search poems with filters
- `GET /api/search/autocomplete` - Get search suggestions

### Dictionary
- `GET /api/dictionary/{word}` - Get word definition

### Comparative Analysis
- `GET /api/compare/poems?poem_ids=1&poem_ids=2` - Compare poems
- `GET /api/compare/poets?poet_ids=1&poet_ids=2` - Compare poets

## Seed Data

The project includes seed data from two Telugu poets:
- **Vemana** (వేమన) - 100 poems from Vemana Satakam
- **Sumathi Satakam** (సుమతీ శతకము) - 100 poems

To load the seed data:
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

## Future Enhancements

- User authentication and personalized collections
- Contribution system for crowd-sourced metadata
- Mobile application
- Advanced ML-based context recognition
- Audio pronunciation support
- Export functionality (PDF, CSV)
- Multi-language support

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

Open Source - See LICENSE file for details

## Contact

For questions or feedback, please open an issue on the project repository.

---

**పద్యార్చన** - Preserving and celebrating Telugu literary heritage through technology.
