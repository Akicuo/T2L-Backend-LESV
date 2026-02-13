# Time2Log User Backend - Python FastAPI

A lightweight, modular Python implementation of the Time2Log User Backend using FastAPI with Supabase integration.

## Features

- **JWT Authentication** with Supabase JWKS validation
- **HTTP-only Cookies** for secure token storage
- **CORS Support** for SvelteKit frontend
- **Token Caching** (5-minute TTL for JWKS)
- **Role-based Access Control**
- **Native Async/Await** for better performance
- **Auto-generated OpenAPI Docs** at `/docs`
- **Database Schema Discovery** via Supabase RPC
- **Profile Integration** - Fetches user names from `app.profiles` table
- **No C Extension Dependencies** - Pure Python implementation

## Installation

```bash
# Install dependencies
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

4. **Database Requirements**: Ensure these tables exist in your Supabase database:
   - `app.profiles` - User profile data (id, first_name, last_name)
   - `app.pre_defined_activities` - Activity templates
   - `app.activities_assignments` - User activity records

## Running the Server

```bash
# Development
uvicorn main:app --reload --log-level debug

# Production
uvicorn main:app --host 0.0.0.0 --port 8080

# Custom port
uvicorn main:app --host 0.0.0.0 --port 7200
```

---

## API Endpoints

### Public Endpoints

#### Health Check

```
GET /health
GET /api/health
GET /test
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000000"
}
```

---

#### Login

```
POST /api/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "your-password"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJFUzI1NiIsImtpZCI6ImNiZjY3...",
  "token_type": "bearer",
  "user_id": "be4da1a2-76df-4b0d-a669-75de1b2a20c9",
  "email": "user@example.com",
  "role": "authenticated",
  "person_name": "John Doe"
}
```

> **Note:** `person_name` is fetched from `app.profiles` table. Falls back to email if not found.

**Response (401):**
```json
{
  "detail": "Invalid credentials"
}
```

> Sets HTTP-only cookie: `supabase-auth-token`

---

#### Logout

```
POST /api/logout
```

**Response (200):**
```json
{
  "message": "Logged out successfully"
}
```

> Clears the `supabase-auth-token` cookie

---

### Protected Endpoints (Require Authentication)

All protected endpoints require the `supabase-auth-token` cookie or `Authorization: Bearer <token>` header.

---

#### Verify Token

```
GET /api/verify-token
```

**Response (valid token):**
```json
{
  "valid": true,
  "user_id": "be4da1a2-76df-4b0d-a669-75de1b2a20c9",
  "email": "user@example.com",
  "role": "authenticated",
  "person_id": "be4da1a2-76df-4b0d-a669-75de1b2a20c9",
  "person_name": "John Doe"
}
```

> **Note:** `person_id` and `person_name` are fetched from `app.profiles` table.

**Response (invalid/no token):**
```json
{
  "valid": false,
  "user_id": null,
  "email": null,
  "role": null,
  "person_id": null,
  "person_name": null
}
```

---

#### Validate Token (Bearer)

```
POST /api/auth/validate
```

**Headers:**
```
Authorization: Bearer eyJhbGciOiJFUzI1NiIsImtpZCI6ImNiZjY3...
```

**Response (200):**
```json
{
  "valid": true,
  "user_id": "be4da1a2-76df-4b0d-a669-75de1b2a20c9",
  "email": "user@example.com",
  "role": "authenticated"
}
```

**Response (401):**
```json
{
  "detail": "Missing or invalid Authorization header"
}
```

---

#### Get Activity Tags

```
GET /api/activities/tags
```

Returns all predefined activities from `app.pre_defined_activities` table.

**Response (200):**
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "organization_id": "org-uuid",
      "key": "work",
      "label": "Work",
      "description": "Work-related activities",
      "category": "productivity",
      "meta": {},
      "is_active": true,
      "created_at": "2024-01-15T10:00:00",
      "updated_at": "2024-01-15T10:00:00"
    }
  ]
}
```

**Response (400):**
```json
{
  "detail": "No tags found"
}
```

---

#### Get Activity History

```
GET /api/activities/history
```

Returns user's activity assignments from `app.activities_assignments` table.

**Response (200):**
```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "activity_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "be4da1a2-76df-4b0d-a669-75de1b2a20c9",
    "start_time": "2024-01-15T08:00:00+00:00",
    "end_time": "2024-01-15T09:00:00+00:00",
    "notes": "Morning run",
    "created_at": "2024-01-15T09:05:00+00:00",
    "updated_at": "2024-01-15T09:05:00+00:00"
  }
]
```

**Response (400):**
```json
{
  "detail": "No activities found"
}
```

---

#### Create Activity

```
POST /api/activities/create
```

Creates a new activity assignment in `app.activities_assignments` table.

**Request Body:**
```json
{
  "activity": {
    "id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "notes": "Morning workout session",
  "start_time": "2024-01-15T08:00:00",
  "end_time": "2024-01-15T09:30:00"
}
```

**Response (200):**
```json
{
  "message": "Activity created successfully"
}
```

**Response (400):**
```json
{
  "detail": "Missing activity id"
}
```
```json
{
  "detail": "Invalid activity id"
}
```

---

#### Admin: Get Schemas

```
GET /api/admin/schemas
```

**Response (200):**
```json
{
  "tables": ["profiles", "pre_defined_activities", "activities_assignments"],
  "timestamp": "2024-01-15T10:30:00.000000"
}
```

---

## Database Schema

### app.profiles
| Column | Type | Description |
|--------|------|-------------|
| id | uuid | User ID (references auth.users) |
| first_name | text | User's first name |
| last_name | text | User's last name |
| created_at | timestamptz | Creation timestamp |
| updated_at | timestamptz | Update timestamp |

### app.pre_defined_activities
| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Activity ID |
| organization_id | uuid | Organization reference |
| key | text | Activity key |
| label | text | Display label |
| description | text | Activity description |
| category | text | Category name |
| meta | jsonb | Additional metadata |
| is_active | boolean | Active status |
| created_at | timestamptz | Creation timestamp |
| updated_at | timestamptz | Update timestamp |

### app.activities_assignments
| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Assignment ID |
| activity_id | uuid | Reference to pre_defined_activities |
| user_id | uuid | Reference to auth.users |
| start_time | timestamptz | Start timestamp |
| end_time | timestamptz | End timestamp |
| notes | text | User notes |
| created_at | timestamptz | Creation timestamp |
| updated_at | timestamptz | Update timestamp |

---

## Project Structure

```
T2L-Backend-LESV/
├── main.py                     # Application entry point
├── config/
│   └── app_settings.py         # Configuration and environment variables
├── models/
│   ├── auth.py                 # Auth request/response models
│   ├── user.py                 # User-related models
│   ├── jwt.py                  # JWT cache model
│   └── schema.py               # Schema discovery models
├── services/
│   ├── supabase_client.py      # Lightweight HTTP-based Supabase client
│   ├── auth_service.py         # Authentication operations
│   ├── jwt_service.py          # JWT validation with JWKS
│   ├── person_service.py       # Profile data fetching
│   └── schema_service.py       # Database schema discovery
├── api/
│   ├── auth.py                 # Authentication routes
│   ├── admin.py                # Admin routes
│   ├── health.py               # Health check routes
│   └── activities.py           # Activity routes
├── utils/
│   └── cookies.py              # Cookie utilities
├── tests/
│   ├── conftest.py             # Pytest configuration
│   ├── test_auth.py            # Auth endpoint tests
│   ├── test_services.py        # Service layer tests
│   └── test_schema.py          # Schema discovery tests
├── scripts/
│   ├── setup_supabase_functions.sql  # SQL function setup
│   └── test_all_endpoints.py         # Endpoint testing script
├── requirements.txt
└── README.md
```

---

## Testing

### Run Tests
```bash
pytest

# With coverage
pytest --cov=. --cov-report=html
```

### Test All Endpoints
```bash
python scripts/test_all_endpoints.py --user your@email.com --password "your-password"
```

---

## Architecture Notes

### Lightweight Supabase Client
This project uses a custom HTTP-based Supabase client instead of the official `supabase` Python package to avoid:
- Heavy dependencies (pyiceberg, pyroaring)
- C compilation requirements
- Installation failures on Linux/Fedora

### JWT Validation
- Tokens are validated using Supabase JWKS endpoint
- Public keys are cached for 5 minutes
- Audience is validated as `authenticated`

### Profile Integration
- User names are fetched from `app.profiles` table
- Falls back to email if profile not found
- Both login and verify-token endpoints return `person_name`

### Security
- JWT tokens validated using Supabase JWKS endpoint
- HTTP-only cookies prevent XSS attacks
- Row Level Security (RLS) enforced via user token passthrough
- CORS properly configured for frontend origins

---

## Troubleshooting

### Schema Discovery Not Working
1. Ensure you've run `scripts/setup_supabase_functions.sql` in Supabase SQL Editor
2. Check your Supabase URL and KEY in `.env`
3. Check server logs for specific error messages

### 401 Unauthorized on Activities
- Ensure you're logged in (cookie is set)
- Check that the user has RLS permissions on the `app` schema tables
- Verify tables exist: `app.pre_defined_activities`, `app.activities_assignments`

### person_name is null
- Ensure `app.profiles` table exists with correct schema
- Check that the user has a profile record (created automatically via trigger)
- Verify RLS policies allow user to read their own profile

---

## License

MIT License - See LICENSE file for details
