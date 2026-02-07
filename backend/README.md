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
OpenAPI docs are served at `http://127.0.0.1:8000/docs`.

## API Endpoints

| Method | Path                    | Description                          |
|--------|-------------------------|--------------------------------------|
| GET    | `/health`               | Health check                         |
| POST   | `/api/analyze`          | Submit a WAV file for analysis       |
| GET    | `/api/analysis/{id}`    | Retrieve analysis results by UUID    |
| GET    | `/api/references`       | List reference tracks (genre filter) |

### POST /api/analyze

Submit a WAV file as multipart form data:

```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -F "file=@track.wav" \
  -F "genre=rock" \
  -F "recommendation_level=suggestive"
```

### GET /api/analysis/{id}

Retrieve a complete analysis including band metrics, overall metrics, and recommendations:

```bash
curl http://127.0.0.1:8000/api/analysis/550e8400-e29b-41d4-a716-446655440000
```

### GET /api/references

List all reference tracks, optionally filtered by genre:

```bash
curl http://127.0.0.1:8000/api/references?genre=rock
```

## Database

SQLite database is stored at `~/.audio-mastering-tool/audio_mastering.db`. The directory and tables are created automatically on first startup.

### Tables (7 total)

| Table                    | Description                                    |
|--------------------------|------------------------------------------------|
| `analysis`               | Core analysis records for uploaded audio files  |
| `band_metrics`           | Per-frequency-band metrics linked to analysis   |
| `overall_metrics`        | Aggregate metrics for a complete analysis       |
| `reference_tracks`       | Built-in and user-added reference tracks        |
| `reference_band_metrics` | Per-band metrics for reference tracks           |
| `recommendations`        | Band-level mastering recommendations            |
| `user_settings`          | Key-value application settings                  |

### Frequency Band Definitions

| Band      | Range (Hz)    |
|-----------|---------------|
| low       | 20 – 200      |
| low_mid   | 200 – 500     |
| mid       | 500 – 2,000   |
| high_mid  | 2,000 – 6,000 |
| high      | 6,000 – 20,000|

## Logging

- Console output: formatted log lines at the configured LOG_LEVEL.
- File output: `~/.audio-mastering-tool/logs/backend.log` with 10 MB rotation and 5 backups.
- Configure via `LOG_LEVEL` and `LOG_FILE` in `.env`.

## Testing

Run the test suite with pytest:

```bash
pytest tests/ -v
```

## Project Structure

```
backend/
├── api/
│   ├── core/
│   │   ├── config.py          # Application settings (pydantic-settings)
│   │   └── logging.py         # Standard logging configuration
│   ├── repositories/
│   │   ├── base.py            # Generic repository base class
│   │   ├── analysis_repo.py   # Analysis-specific queries
│   │   └── reference_repo.py  # Reference track queries
│   ├── routers/
│   │   ├── health.py          # Health check endpoint
│   │   ├── analyze.py         # Analysis endpoints
│   │   └── references.py      # Reference track endpoints
│   ├── database.py            # Synchronous SQLAlchemy engine/session
│   ├── main.py                # FastAPI app entry point
│   ├── models.py              # SQLAlchemy ORM models (7 tables)
│   └── schemas.py             # Pydantic request/response models
├── config/
│   ├── __init__.py
│   └── constants.py           # Band definitions, genres, recommendation levels
├── database/
│   └── migrations/
│       └── init_schema.sql    # Reference SQL schema
├── utils/
│   ├── logger.py              # Logging convenience wrapper
│   └── errors.py              # Custom exception hierarchy
├── tests/
│   ├── conftest.py            # Pytest fixtures
│   ├── test_database.py       # Schema and table tests
│   ├── test_repositories.py   # Repository CRUD tests
│   └── test_api.py            # HTTP endpoint tests
├── .env.example
├── requirements.txt
├── README.md
└── ARCHITECTURE.md
```

## Troubleshooting

- **Database not created**: Ensure the `~/.audio-mastering-tool/` directory is writable.
- **Import errors**: Make sure you run commands from the `backend/` directory.
- **Port already in use**: Change `API_PORT` in `.env` or stop the conflicting process.
