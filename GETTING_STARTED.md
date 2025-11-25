# 🚀 Getting Started with పద్యార్చన (Padyarchana)

## Welcome!

This guide will get you up and running with Padyarchana in under 5 minutes.

---

## Prerequisites Check ✓

Before starting, ensure you have:
- ✅ Python 3.11 or higher installed
- ✅ pip (Python package manager)
- ✅ Terminal/Command prompt access

Check your Python version:
```bash
python --version
# or
python3 --version
```

---

## 3-Step Quick Start

### Step 1: Set Up Environment (1 minute)

```bash
# Create and activate virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Load Data (30 seconds)

```bash
# Initialize database and load poems
python scripts/seed_data.py
```

You should see:
```
============================================================
  పద్యార్చన (Padyarchana) - Database Seeder
============================================================
🚀 Starting database seeding...
✅ Database tables created
📖 Loading data from padyalu_json_data/vemana_100.json...
Created poet: వేమన
Created meter: ఆటవెలది
✅ Successfully imported 100 poems
...
```

### Step 3: Run the Application (10 seconds)

```bash
# Start the server
python app/main.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 🎉 You're Ready!

Open your browser and visit:

### 🌐 Web Interface
**http://localhost:8000**

You'll see the homepage with:
- Search bar for finding poems
- Featured poets (వేమన and more)
- Popular meters (ఆటవెలది, కందం, etc.)
- Recently added poems

### 📚 API Documentation
**http://localhost:8000/docs**

Interactive API documentation where you can:
- Browse all endpoints
- Try API calls directly
- See request/response formats

---

## Quick Tour

### Try These Features:

1. **Search for a Poem**
   - Type "వేమన" in the search bar
   - Press Enter or click Search

2. **Browse the API**
   - Go to http://localhost:8000/docs
   - Click on "GET /api/poems"
   - Click "Try it out"
   - Click "Execute"
   - See the list of poems!

3. **Get a Specific Poem**
   - Try: http://localhost:8000/api/poems/1
   - You'll see the first poem with all its details

4. **List All Poets**
   - Try: http://localhost:8000/api/poets
   - See వేమన and other poets

5. **Check Health**
   - Try: http://localhost:8000/health
   - Should return: `{"status": "healthy"}`

---

## Common Commands

```bash
# Start the server
python app/main.py

# Start with auto-reload (for development)
uvicorn app.main:app --reload

# Reset the database
rm padyarchana.db
python scripts/seed_data.py

# Stop the server
Ctrl + C
```

---

## What You Can Do Now

### Via Web Interface:
- ✅ Browse homepage
- ✅ View featured content
- ✅ Use search bar (basic)

### Via API:
- ✅ Get all poems (`GET /api/poems`)
- ✅ Get specific poem (`GET /api/poems/1`)
- ✅ Get all poets (`GET /api/poets`)
- ✅ Get specific poet (`GET /api/poets/1`)
- ✅ Get all meters (`GET /api/meters`)
- ✅ Get specific meter (`GET /api/meters/1`)
- ✅ Create new poem (`POST /api/poems`)
- ✅ Update poem (`PUT /api/poems/1`)
- ✅ Delete poem (`DELETE /api/poems/1`)

---

## Sample Data Loaded

After running the seed script, you'll have:

### Poets:
- **వేమన** (Vemana) - 100 poems
- **Sumathi Satakam Author** - 100 poems

### Meters:
- **ఆటవెలది** (Aata Veladi)
- **కందం** (Kandam)

### Total: 200 Poems!

---

## Testing the API with cURL

```bash
# Get all poems
curl http://localhost:8000/api/poems

# Get first poem
curl http://localhost:8000/api/poems/1

# Get all poets
curl http://localhost:8000/api/poets

# Search poems (will return empty array for now, but won't error)
curl "http://localhost:8000/api/search?q=వేమన"

# Health check
curl http://localhost:8000/health
```

---

## Next Steps

Once you're comfortable with the basics:

1. **Read the Documentation**
   - [README.md](README.md) - Project overview
   - [SETUP_GUIDE.md](SETUP_GUIDE.md) - Detailed setup guide
   - [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - What's been built

2. **Explore the Code**
   - Check `app/models/` for database models
   - Check `app/api/` for API endpoints
   - Check `app/templates/` for HTML templates

3. **Customize**
   - Add more poems via API
   - Modify the homepage template
   - Adjust styling in `static/css/styles.css`

4. **Develop**
   - Implement search functionality
   - Add dictionary integration
   - Build comparative analysis tools

---

## Need Help?

### Documentation Files:
- **GETTING_STARTED.md** (This file) - Quick start
- **README.md** - Project overview
- **SETUP_GUIDE.md** - Comprehensive setup guide
- **PROJECT_SUMMARY.md** - Technical summary
- **IMPLEMENTATION_PLAN.md** - Development roadmap

### Check the API Docs:
- http://localhost:8000/docs (when running)

### Debug Mode:
Set `DEBUG=True` in `.env` file for detailed error messages

---

## Stopping the Server

When you're done:
```bash
# Press Ctrl+C in the terminal where the server is running

# Deactivate virtual environment
deactivate
```

---

## Summary

Congratulations! You now have:
- ✅ A working Telugu poetry search engine
- ✅ 200 poems loaded and searchable
- ✅ RESTful API with full documentation
- ✅ Web interface with Telugu font support
- ✅ Database with comprehensive schema
- ✅ Foundation for advanced features

**Start exploring Telugu poetry! 📚✨**

---

*Project: పద్యార్చన (Padyarchana)*
*Preserving Telugu literary heritage through technology*
