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

| Method | Path                            | Description                              |
|--------|---------------------------------|------------------------------------------|
| GET    | `/health`                       | Health check                             |
| POST   | `/api/analyze`                  | Submit a WAV file for analysis           |
| GET    | `/api/analysis/{id}`            | Retrieve analysis results by UUID        |
| GET    | `/api/references`               | List reference tracks (genre filter)     |
| POST   | `/api/similarity/{analysis_id}` | Find similar reference tracks            |

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

### POST /api/similarity/{analysis_id}

Find reference tracks most similar to a completed analysis:

```bash
curl -X POST http://127.0.0.1:8000/api/similarity/550e8400-e29b-41d4-a716-446655440000
```

With genre filter and custom result count:

```bash
curl -X POST "http://127.0.0.1:8000/api/similarity/550e8400-e29b-41d4-a716-446655440000?genre=Psytrance&top_k=5"
```

## Database

SQLite database is stored at `~/.audio-mastering-tool/audio_mastering.db`. The directory and tables are created automatically on first startup.

### Tables (8 total)

| Table                       | Description                                    |
|-----------------------------|------------------------------------------------|
| `analysis`                  | Core analysis records for uploaded audio files  |
| `band_metrics`              | Per-frequency-band metrics linked to analysis   |
| `overall_metrics`           | Aggregate metrics for a complete analysis       |
| `reference_tracks`          | Built-in and user-added reference tracks        |
| `reference_band_metrics`    | Per-band metrics for reference tracks           |
| `reference_overall_metrics` | Aggregate metrics for reference tracks          |
| `recommendations`           | Band-level mastering recommendations            |
| `user_settings`             | Key-value application settings                  |

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

## Reference Database

The application ships with 24 built-in electronic music reference tracks spanning Psytrance, Trance, Techno, House, Drum & Bass, and Dubstep. Each reference has pre-computed per-band metrics, overall metrics, and a 128-dimensional feature vector for similarity matching.

### Populating References

Run the population script from the `backend/` directory:

```bash
python -m scripts.populate_references
```

To replace all existing built-in references:

```bash
python -m scripts.populate_references --force
```

### Analyzing Real Audio as References

To add a real audio file as a reference track:

```bash
python -m scripts.analyze_reference path/to/track.wav \
    --name "Track Name" --artist "Artist" --genre "Psytrance" --year 2020
```

## Similarity Search

The similarity search uses a 128-dimensional feature vector extracted from analysis metrics and cosine similarity to rank reference tracks.

### Feature Vector Composition (128 dimensions)

| Category              | Features                                                    | Dims |
|-----------------------|-------------------------------------------------------------|------|
| Spectral              | Centroid, Rolloff, Flatness, Energy per band + aggregates   | 40   |
| Dynamics              | LUFS, LRA, True Peak, DR, Crest Factor + per-band stats    | 20   |
| Energy Distribution   | Normalized energy per band                                  | 5    |
| Stereo                | Width, Phase Correlation per band + overall                 | 10   |
| Harmonic/Transient    | THD, Harmonic Ratio, Transient Preservation, Attack Time    | 8    |
| Reserved              | Padding for future features                                 | 45   |

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
│   │   └── reference_repo.py  # Reference track queries + similarity search
│   ├── routers/
│   │   ├── health.py          # Health check endpoint
│   │   ├── analyze.py         # Analysis endpoints
│   │   └── references.py      # Reference track + similarity endpoints
│   ├── database.py            # Synchronous SQLAlchemy engine/session
│   ├── main.py                # FastAPI app entry point
│   ├── models.py              # SQLAlchemy ORM models (8 tables)
│   └── schemas.py             # Pydantic request/response models
├── ml/
│   ├── __init__.py
│   ├── feature_extraction.py  # 128-dim feature vector extraction
│   ├── similarity.py          # Cosine similarity matching + serialization
│   └── tests/
│       ├── test_feature_extraction.py
│       └── test_similarity.py
├── scripts/
│   ├── populate_references.py # Reference database population script
│   └── analyze_reference.py   # Analyze real audio as reference track
├── data/
│   └── references/
│       └── reference_metadata.json  # Electronic music reference metadata
├── config/
│   ├── __init__.py
│   └── constants.py           # Band definitions, genres, recommendation levels
├── database/
│   └── migrations/
│       ├── init_schema.sql    # Reference SQL schema
│       └── add_reference_overall_metrics.sql
├── utils/
│   ├── logger.py              # Logging convenience wrapper
│   └── errors.py              # Custom exception hierarchy
├── tests/
│   ├── conftest.py            # Pytest fixtures
│   ├── test_database.py       # Schema and table tests
│   ├── test_repositories.py   # Repository CRUD tests
│   ├── test_api.py            # HTTP endpoint tests
│   └── test_similarity_endpoint.py  # Similarity search integration tests
├── .env.example
├── requirements.txt
├── README.md
└── ARCHITECTURE.md
```

## Troubleshooting

- **Database not created**: Ensure the `~/.audio-mastering-tool/` directory is writable.
- **Import errors**: Make sure you run commands from the `backend/` directory.
- **Port already in use**: Change `API_PORT` in `.env` or stop the conflicting process.
