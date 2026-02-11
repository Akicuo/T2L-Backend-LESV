# Time2Log User Backend - Python FastAPI

A simpler, shorter Python implementation of the Time2Log User Backend using FastAPI.

## Features

- **JWT Authentication** with Supabase JWKS validation
- **HTTP-only Cookies** for secure token storage
- **CORS Support** for React frontend
- **Token Caching** (5-minute TTL for JWKS)
- **Role-based Access Control**
- **Async/Await** for better performance
- **Auto-generated OpenAPI Docs** at `/docs`

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or with uv (much faster)
pip install uv
uv pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and fill in your Supabase credentials:

```bash
cp .env.example .env
```

## Running the Server

```bash
# Development
uvicorn main:app --reload

# Production
uvicorn main:app --host 0.0.0.0 --port 8080

# Or directly
python main.py
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/login` | User login with email/password |
| GET | `/api/verify-token` | Validate JWT from cookie |
| POST | `/api/logout` | Clear auth cookie |
| POST | `/api/auth/validate` | Legacy Bearer token validation |
| GET | `/health` | Health check |
| GET | `/docs` | Interactive API documentation (Swagger UI) |

## Comparison with Java Implementation

| Aspect | Java (Spring) | Python (FastAPI) |
|--------|---------------|------------------|
| Lines of Code | ~1500+ | ~400 |
| Startup Time | ~2-3s | ~0.5s |
| Memory Usage | ~200-400MB | ~30-50MB |
| Dependencies | 20+ | 7 |
| Async Support | Reactive (WebFlux) | Native (asyncio) |

## Code Structure

```
main.py
├── Configuration (Settings)
├── Models (Pydantic)
├── JWKS Key Cache
├── Services
│   ├── JwtService (JWT validation)
│   └── SupabaseAuthService (Auth client)
├── Cookie Utilities
├── Dependencies (auth, role check)
└── Routes (all endpoints)
```

## Development

```bash
# Run with hot reload
uvicorn main:app --reload --log-level debug

# View API docs
# Open http://localhost:8080/docs
```
