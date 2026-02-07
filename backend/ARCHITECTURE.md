# Architecture

This document describes the backend architecture decisions and design patterns.

## Repository Pattern

All database access goes through repository classes that extend `BaseRepository[ModelT]`. This provides:

- **Consistent CRUD interface**: Every model gets `get_by_id`, `get_all`, `create`, `update`, `delete` for free.
- **Eager-loading control**: Specialised repositories (e.g. `AnalysisRepository`) define methods that load related entities via `joinedload` / `selectinload` to avoid N+1 queries.
- **Testability**: Repositories accept a `Session` instance, making it easy to inject an in-memory test database.

### Class hierarchy

```
BaseRepository[ModelT]
├── AnalysisRepository      – analysis + band_metrics, overall_metrics, recommendations
└── ReferenceRepository     – reference_tracks + reference_band_metrics
```

## Database Schema Design

All primary keys are UUID v4 strings stored as `TEXT`. This allows IDs to be generated client-side without database round-trips and avoids integer ID enumeration.

Foreign keys use `ON DELETE CASCADE` so that deleting a parent row (e.g. an analysis) automatically removes its child metrics and recommendations.

Indexes are placed on:
- Foreign key columns (for join performance)
- `band_name` columns (for per-band filtering)
- `genre` and `is_builtin` on reference tracks (for common query patterns)
- `severity` on recommendations (for priority-based filtering)

## Frequency Band Definitions

Defined in `config/constants.py`, the five frequency bands partition the audible spectrum:

| Band     | Hz Range       | Musical Role                |
|----------|----------------|-----------------------------|
| low      | 20 – 200       | Sub-bass and bass fundamentals |
| low_mid  | 200 – 500      | Warmth and body              |
| mid      | 500 – 2,000    | Presence and vocal clarity   |
| high_mid | 2,000 – 6,000  | Brightness and detail        |
| high     | 6,000 – 20,000 | Air and brilliance           |

Each `BandMetrics` / `ReferenceBandMetrics` row stores `freq_min` and `freq_max` alongside the band name for self-describing data.

## Key Flows

### Analysis submission (stub)

```
Client  --->  POST /api/analyze (file + form data)
               │
               ├── Validate upload
               ├── Generate UUID
               └── Return stub response
               (DSP pipeline integration is a future ticket)
```

### Analysis retrieval

```
Client  --->  GET /api/analysis/{id}
               │
               ├── AnalysisRepository.get_with_metrics(id)
               │     └── SELECT analysis JOIN band_metrics JOIN overall_metrics
               ├── 404 if not found
               └── Return AnalysisResponse (Pydantic model)
```

### Reference listing

```
Client  --->  GET /api/references?genre=rock
               │
               ├── ReferenceRepository.get_by_genre("rock")  OR  get_all()
               └── Return list[ReferenceTrackResponse]
```

## Logging

Standard Python `logging` with two handlers:

1. **Console** (`StreamHandler`): Concise format for development.
2. **File** (`RotatingFileHandler`): Detailed format with module/line numbers, 10 MB rotation, 5 backups.

## Error Handling

Custom exceptions inherit from `AudioMasteringError` (defined in `utils/errors.py`):

```
AudioMasteringError
├── DatabaseError
├── ValidationError
├── FileNotFoundError
└── AnalysisError
```

API endpoints catch known exceptions and return appropriate HTTP status codes. Unknown exceptions propagate to FastAPI's default 500 handler.
