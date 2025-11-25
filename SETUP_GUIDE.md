# పద్యార్చన (Padyarchana) - Setup & Usage Guide

## Quick Start Guide

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)
- Git (optional, for version control)

### Step-by-Step Setup

#### 1. Set up Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env if needed (optional - defaults work fine for development)
```

#### 4. Initialize Database and Load Seed Data

```bash
# This will create the database and load the Telugu poetry data
python scripts/seed_data.py
```

Expected output:
```
============================================================
  పద్యార్చన (Padyarchana) - Database Seeder
============================================================
🚀 Starting database seeding...
📋 Creating database tables...
✅ Database tables created
📖 Loading data from padyalu_json_data/vemana_100.json...
Created poet: వేమన
Created meter: ఆటవెలది
📝 Processing 100 poems...
✅ Successfully imported 100 poems
...
```

#### 5. Run the Application

```bash
# Option 1: Using the main script
python app/main.py

# Option 2: Using uvicorn directly (recommended for development)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 6. Access the Application

Open your browser and navigate to:
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

## Project Structure Explained

```
padyarchana_prototype/
├── app/                        # Main application directory
│   ├── api/                    # API endpoint handlers
│   │   ├── poems.py            # Poems CRUD endpoints
│   │   ├── poets.py            # Poets CRUD endpoints
│   │   ├── meters.py           # Meters CRUD endpoints
│   │   ├── search.py           # Search functionality
│   │   ├── dictionary.py       # Dictionary lookups
│   │   └── compare.py          # Comparative analysis
│   ├── models/                 # Database models (SQLAlchemy)
│   │   ├── poem.py             # Poem model
│   │   ├── poet.py             # Poet model
│   │   ├── meter.py            # Meter/Chandassu model
│   │   ├── dictionary.py       # Word and PoemWord models
│   │   ├── sandhi.py           # Sandhi model
│   │   ├── samasa.py           # Samasa model
│   │   ├── gana.py             # Gana model
│   │   ├── yati.py             # Yati model
│   │   └── prasa.py            # Prasa model
│   ├── schemas/                # Pydantic validation schemas
│   │   ├── poem.py
│   │   ├── poet.py
│   │   └── meter.py
│   ├── templates/              # HTML templates (Jinja2)
│   │   ├── base.html           # Base template
│   │   └── index.html          # Homepage
│   ├── config.py               # Configuration settings
│   ├── database.py             # Database connection setup
│   └── main.py                 # FastAPI app entry point
├── static/                     # Static files
│   ├── css/
│   │   └── styles.css          # Custom styles
│   └── js/
│       └── app.js              # JavaScript utilities
├── scripts/                    # Utility scripts
│   └── seed_data.py            # Database seeding script
├── padyalu_json_data/          # Seed data (JSON files)
│   ├── vemana_100.json         # Vemana poems
│   └── sumathii_satakam.json   # Sumathi Satakam poems
├── data/                       # Data directory (for additional data)
├── tests/                      # Test files
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── README.md                   # Project README
├── IMPLEMENTATION_PLAN.md      # Detailed implementation plan
└── SETUP_GUIDE.md              # This file
```

## Database Schema

### Core Tables

#### Poets
- `id`: Primary key
- `name`: Poet name in Telugu
- `name_english`: English transliteration
- `biography`: Biography text
- `era`: Time period (కాలం)
- `birth_year`, `death_year`: Lifespan

#### Meters (Chandassu)
- `id`: Primary key
- `name`: Meter name in Telugu
- `name_english`: English transliteration
- `description`: Description
- `gana_structure`: JSON field for gana pattern
- `example_pattern`: Example pattern

#### Poems
- `id`: Primary key
- `title`: Poem title
- `text`: Full poem text
- `literary_form`: పద్య రకం
- `word_count`, `gana_count`, `line_count`: Statistics
- `poet_id`: Foreign key to Poets
- `meter_id`: Foreign key to Meters
- `created_at`, `updated_at`: Timestamps

#### Metadata Tables
- **Words**: Dictionary entries
- **PoemWords**: Words in poems with positions
- **Sandhi**: Euphonic combinations
- **Samasa**: Compound words
- **Ganas**: Prosodic feet
- **Yati**: Caesura information
- **Prasa**: Rhyme/alliteration

## API Endpoints Reference

### Poems API

```bash
# Get all poems (paginated)
GET /api/poems?skip=0&limit=10

# Get specific poem
GET /api/poems/1

# Create new poem
POST /api/poems
{
  "title": "పద్య శీర్షిక",
  "text": "పద్య పాఠం...",
  "poet_id": 1,
  "meter_id": 1
}

# Update poem
PUT /api/poems/1
{
  "title": "Updated Title"
}

# Delete poem
DELETE /api/poems/1
```

### Poets API

```bash
# Get all poets
GET /api/poets?skip=0&limit=10

# Get specific poet
GET /api/poets/1

# Create new poet
POST /api/poets
{
  "name": "వేమన",
  "era": "Medieval"
}
```

### Meters API

```bash
# Get all meters
GET /api/meters?skip=0&limit=10

# Get specific meter
GET /api/meters/1

# Create new meter
POST /api/meters
{
  "name": "ఆటవెలది",
  "description": "..."
}
```

### Search API

```bash
# Search poems
GET /api/search?q=వేమన&poet_id=1&meter_id=1

# Autocomplete
GET /api/search/autocomplete?q=వేమ
```

### Dictionary API

```bash
# Look up word
GET /api/dictionary/పద్యం
```

### Comparison API

```bash
# Compare poems
GET /api/compare/poems?poem_ids=1&poem_ids=2

# Compare poets
GET /api/compare/poets?poet_ids=1&poet_ids=2
```

## Testing the Application

### Using the Web Interface

1. **Homepage** (http://localhost:8000)
   - Use the search bar to search for poems
   - Browse featured poets and meters
   - Click on any item to view details

2. **API Documentation** (http://localhost:8000/docs)
   - Interactive API documentation
   - Try out API endpoints directly
   - See request/response schemas

### Using cURL

```bash
# Get all poems
curl http://localhost:8000/api/poems

# Get specific poem
curl http://localhost:8000/api/poems/1

# Search poems
curl "http://localhost:8000/api/search?q=వేమన"

# Health check
curl http://localhost:8000/health
```

### Using Python

```python
import requests

# Get all poems
response = requests.get("http://localhost:8000/api/poems")
poems = response.json()
print(f"Found {len(poems)} poems")

# Get specific poem
poem = requests.get("http://localhost:8000/api/poems/1").json()
print(poem["title"])
```

## Current Status

### ✅ Completed Features

1. **Project Structure**: Complete directory structure set up
2. **Database Models**: All 10 models implemented (Poet, Meter, Poem, Word, PoemWord, Sandhi, Samasa, Gana, Yati, Prasa)
3. **Database Configuration**: SQLite with async support
4. **API Endpoints**: CRUD operations for Poems, Poets, and Meters
5. **Seed Data Script**: Automatic data loading from JSON files
6. **Frontend Structure**: Base templates and homepage with Alpine.js
7. **Styling**: Custom CSS with Telugu font support
8. **Configuration**: Environment-based settings

### 🚧 Next Steps (Future Development)

1. **Advanced Search**
   - Full-text search with SQLite FTS5
   - Complex filtering by metadata
   - Real autocomplete implementation

2. **Telugu NLP Services**
   - Chandassu/Meter identification
   - Sandhi detection and classification
   - Samasa identification
   - Gana breakdown
   - Yati and Prasa verification

3. **Dictionary Integration**
   - Load Telugu dictionary data
   - Implement word lookup
   - Add pronunciation support

4. **Hyperlinked Poem View**
   - Make words clickable
   - Show definitions in modal/sidebar
   - Display grammatical analysis

5. **Comparative Analysis**
   - Poem comparison logic
   - Poet similarity analysis
   - Statistical visualizations

6. **Additional Pages**
   - Detailed search results page
   - Individual poem view page
   - Poet profile pages
   - Meter information pages
   - About page

## Troubleshooting

### Port Already in Use

If port 8000 is already in use:
```bash
# Use a different port
uvicorn app.main:app --port 8001
```

### Module Not Found Errors

Make sure you're in the virtual environment:
```bash
# Check if venv is activated (should show (venv) in prompt)
which python

# If not, activate it
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

### Database Errors

Reset the database:
```bash
# Delete the database file
rm padyarchana.db

# Re-run the seed script
python scripts/seed_data.py
```

### Telugu Font Not Displaying

Make sure your browser supports Telugu fonts or install:
- Noto Sans Telugu
- Tiro Telugu

## Development Workflow

### Making Changes

1. **Backend Changes** (Python/FastAPI)
   - Edit files in `app/` directory
   - Server will auto-reload in development mode

2. **Frontend Changes** (HTML/CSS/JS)
   - Edit templates in `app/templates/`
   - Edit styles in `static/css/`
   - Refresh browser to see changes

3. **Database Changes**
   - Edit models in `app/models/`
   - Re-run seed script to reset database

### Code Quality

```bash
# Format code
black app/ scripts/

# Lint code
flake8 app/ scripts/

# Run tests (when implemented)
pytest
```

## Support

For issues or questions:
1. Check this guide
2. Review the IMPLEMENTATION_PLAN.md
3. Check API documentation at /docs
4. Review code comments

---

**Happy coding! 🎉**

Preserving Telugu literary heritage through technology.
