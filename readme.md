    # Time2Log User Backend - Python FastAPI

A lightweight, modular Python implementation of the Time2Log User Backend using FastAPI with Supabase integration.

## Features

- **JWT Authentication** with Supabase JWKS validation
- **HTTP-only Cookies** for secure token storage
- **CORS Support** for React frontend
- **Token Caching** (5-minute TTL for JWKS)
- **Role-based Access Control**
- **Native Async/Await** for better performance
- **Auto-generated OpenAPI Docs** at `/docs`
- **Database Schema Discovery** via Supabase RPC
- **No C Extension Dependencies** - Pure Python implementation

## Installation

```bash
# Install dependencies (no C compilation required)
pip install -r requirements.txt

# Or with uv (much faster)
pip install uv
uv pip install -r requirements.txt
```

## Configuration

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` with your Supabase credentials

3. **Important**: Run the SQL setup script in Supabase SQL Editor:
```bash
# Copy and paste the contents of scripts/setup_supabase_functions.sql
# into your Supabase SQL Editor
```

## Running the Server

```bash
# Development
python main.py

# Or with uvicorn directly
uvicorn main:app --reload

# Production
uvicorn main:app --host 0.0.0.0 --port 8080
```

## API Endpoints

| Method | Path | Description | Auth Required |
|--------|------|-------------|----------------|
| POST | `/api/login` | User login with email/password | No |
| GET | `/api/verify-token` | Validate JWT from cookie | No |
| POST | `/api/logout` | Clear auth cookie | No |
| POST | `/api/auth/validate` | Legacy Bearer token validation | No |
| GET | `/health` | Health check | No |
| GET | `/api/admin/schemas` | Database schema discovery | Optional |
| GET | `/api/test` | Simple test endpoint | No |
| GET | `/docs` | Interactive API documentation (Swagger UI) | No |

## Project Structure

```
T2L-Backend-LESV/
├── main.py                     # Application entry point
├── config/
│   ├── settings.py             # Configuration and environment variables
│   └── __init__.py
├── models/
│   ├── auth.py                # Auth request/response models
│   ├── user.py                # User-related models
│   ├── jwt.py                 # JWT cache model
│   ├── schema.py              # Schema discovery models
│   └── __init__.py
├── services/
│   ├── supabase_client.py      # Lightweight HTTP-based Supabase client
│   ├── auth_service.py         # Authentication operations
│   ├── jwt_service.py          # JWT validation
│   ├── schema_service.py       # Database schema discovery
│   └── __init__.py
├── api/
│   ├── auth.py                # Authentication routes
│   ├── admin.py               # Admin routes
│   ├── health.py              # Health check routes
│   └── __init__.py
├── utils/
│   ├── cookies.py             # Cookie utilities
│   └── __init__.py
├── tests/
│   ├── conftest.py           # Pytest configuration
│   ├── test_auth.py          # Auth endpoint tests
│   ├── test_services.py       # Service layer tests
│   ├── test_schema.py        # Schema discovery tests
│   └── __init__.py
├── scripts/
│   ├── setup_supabase_functions.sql  # SQL function setup
│   └── test_manual.py              # Manual testing script
├── requirements.txt
├── pyproject.toml
└── readme.md
```

## Comparison with Java Implementation

| Aspect | Java (Spring) | Python (FastAPI) |
|--------|---------------|------------------|
| Lines of Code | ~1500+ | ~600 |
| Startup Time | ~2-3s | ~0.5s |
| Memory Usage | ~200-400MB | ~30-50MB |
| Dependencies | 20+ | 9 (no C extensions) |
| Async Support | Reactive (WebFlux) | Native (asyncio) |
| Modularity | Monolithic | Layered/Modular |

## Development

```bash
# Run with hot reload
uvicorn main:app --reload --log-level debug

# View API docs
# Open http://localhost:8080/docs

# Run tests
pytest

# Run manual test script
python scripts/test_manual.py
```

## Architecture Notes

### Lightweight Supabase Client
This project uses a custom HTTP-based Supabase client instead of the official `supabase` Python package to avoid:
- Heavy dependencies (pyiceberg, pyroaring)
- C compilation requirements
- Installation failures on Linux/Fedora

The client implements only the required features:
- Authentication (sign-in, sign-out, get user)
- Database operations (select, insert, update, delete)
- RPC function calls for schema discovery

### Schema Discovery
Database schema discovery uses Supabase RPC (Remote Procedure Call) functions:
1. `get_tables()` - Lists all tables in public schema
2. `get_table_columns(table_name)` - Gets column info for a table
3. `get_table_count(table_name)` - Gets row count for a table

These functions must be created in your Supabase database by running the SQL script at `scripts/setup_supabase_functions.sql`.

### Security
- JWT tokens validated using Supabase JWKS endpoint
- HTTP-only cookies prevent XSS attacks
- Role-based access control for protected endpoints
- CORS properly configured for frontend origins

## Testing

The project includes:
- **Unit tests** for services (`tests/test_services.py`)
- **Integration tests** for API endpoints (`tests/test_auth.py`)
- **Manual testing script** (`scripts/test_manual.py`)

Run tests with:
```bash
pytest

# Or with coverage
pytest --cov=. --cov-report=html
```

## Troubleshooting

### Linux/Fedora Installation Issues
If you encounter C compilation errors with `pyiceberg` or `pyroaring`:
- This project no longer uses the `supabase` package
- All dependencies are pure Python with no C extensions
- Just run `pip install -r requirements.txt`

### Schema Discovery Not Working
1. Ensure you've run `scripts/setup_supabase_functions.sql` in Supabase SQL Editor
2. Check your Supabase URL and KEY in `.env`
3. Check server logs for specific error messages

## License

MIT License - See LICENSE file for details
