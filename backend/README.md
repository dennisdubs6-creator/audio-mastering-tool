# Audio Mastering Tool - Backend

FastAPI backend for the Audio Mastering Analysis application.

## Setup

1. Create and activate a virtual environment:

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy the environment file and adjust as needed:

```bash
cp .env.example .env
```

## Running

Start the development server:

```bash
uvicorn api.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/analyze` | Submit a WAV file for analysis |
| GET | `/api/analysis/{id}` | Retrieve analysis results |
| GET | `/api/references` | List reference tracks |

## Database

SQLite database is stored at `~/.audio-mastering-tool/audio_mastering.db`. The directory and tables are created automatically on first startup.

## Project Structure

```
backend/
├── api/
│   ├── core/
│   │   ├── config.py        # Application settings
│   │   └── logging.py       # Loguru configuration
│   ├── repositories/
│   │   ├── base.py           # Generic repository base class
│   │   └── analysis_repo.py  # Analysis-specific queries
│   ├── routers/
│   │   ├── health.py         # Health check endpoint
│   │   ├── analyze.py        # Analysis endpoints
│   │   └── references.py     # Reference track endpoints
│   ├── database.py           # Async SQLAlchemy engine/session
│   ├── main.py               # FastAPI app entry point
│   └── models.py             # SQLAlchemy ORM models (7 tables)
├── .env.example
├── requirements.txt
└── README.md
```
