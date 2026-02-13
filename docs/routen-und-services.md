# Routen und Services Dokumentation

Diese Dokumentation erklärt, wie man neue Routen erstellt, den Supabase Client verwendet und neue Funktionalität zum Backend hinzufügt.

---

## Inhaltsverzeichnis

1. [Neue Route erstellen](#neue-route-erstellen)
2. [Geschützte vs. Ungeschützte Routen](#geschützte-vs-ungeschützte-routen)
3. [Router in main.py registrieren](#router-in-mainpy-registrieren)
4. [Supabase Client verwenden](#supabase-client-verwenden)
5. [Neue Funktionalität hinzufügen](#neue-funktionalität-hinzufügen)
6. [Best Practices](#best-practices)

---

## Neue Route erstellen

### Schritt 1: Neue Datei im `api/` Ordner erstellen

Erstelle eine neue Datei im `api/` Ordner, z.B. `api/meine_routen.py`:

```python
"""
Meine eigenen Routen
"""
import logging
from fastapi import APIRouter, HTTPException, Depends

from models.user import TokenMetadata
from services.supabase_client import supabase_client
from utils.cookies import get_token_from_cookie

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["MeineRouten"])
```

### Schritt 2: Route definieren

```python
@router.get("/meine-endpoint")
async def meine_funktion():
    """Beschreibung der Route"""
    return {"message": "Hallo Welt"}
```

---

## Geschützte vs. Ungeschützte Routen

### Ungeschützte Route (öffentlich zugänglich)

```python
@router.get("/oeffentliche-daten")
async def oeffentliche_daten():
    """Diese Route ist für jeden zugänglich"""
    daten = await supabase_client.table_select("oeffentliche_tabelle")
    return {"daten": daten}
```

### Geschützte Route (Authentifizierung erforderlich)

Es gibt zwei Möglichkeiten, Routen zu schützen:

#### Option 1: Mit `get_token_from_cookie` Dependency

```python
from utils.cookies import get_token_from_cookie
from services.jwt_service import JwtService

@router.get("/meine-geschuetzten-daten")
async def geschuetzte_daten(token = Depends(get_token_from_cookie)):
    """Diese Route erfordert Authentifizierung"""

    # Token validieren
    if not token:
        raise HTTPException(status_code=401, detail="Nicht authentifiziert")

    metadata = await JwtService.validate_token(token)
    if not metadata:
        raise HTTPException(status_code=401, detail="Ungültiger Token")

    # Jetzt kannst du metadata.user_id, metadata.email etc. verwenden
    daten = await supabase_client.table_select(
        "benutzer_daten",
        filters={"user_id": metadata.user_id}
    )

    return {"daten": daten, "user": metadata.email}
```

#### Option 2: Mit der `_get_current_user` Helper-Funktion

```python
async def _get_current_user(token: str | None) -> TokenMetadata:
    """
    Hilfsfunktion zur Benutzer-Authentifizierung mit Dev-Bypass.
    """
    from config import settings

    # Dev-Modus: Auth umgehen
    if settings.ENVIRONMENT == "development" and settings.DISABLE_AUTH:
        return TokenMetadata(
            user_id="dev-user",
            email="dev@example.com",
            role="admin",
            person_id=None,
            person_name="Dev User",
        )

    if not token:
        raise HTTPException(status_code=401, detail="Nicht authentifiziert")

    metadata = await JwtService.validate_token(token)
    if not metadata:
        raise HTTPException(status_code=401, detail="Ungültiger Token")

    return metadata


@router.get("/meine-daten")
async def meine_daten(token = Depends(get_token_from_cookie)):
    """Geschützte Route mit Helper-Funktion"""
    user = await _get_current_user(token)

    # user.user_id, user.email, user.role sind jetzt verfügbar
    return {"user_id": user.user_id, "email": user.email}
```

### Rollenbasierte Zugriffskontrolle

```python
@router.get("/admin-only")
async def admin_only(token = Depends(get_token_from_cookie)):
    """Nur für Admins zugänglich"""
    user = await _get_current_user(token)

    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Keine Berechtigung")

    return {"message": "Willkommen, Admin!"}
```

---

## Router in main.py registrieren

**WICHTIG:** Nach dem Erstellen eines neuen Routers muss dieser in `main.py` registriert werden!

### Schritt 1: Router importieren

Öffne `main.py` und füge den Import hinzu:

```python
# Import routers
from api.auth import router as auth_router
from api.admin import router as admin_router
from api.health import router as health_router
from api.activities import router as activities_router
from api.meine_routen import router as meine_routen_router  # <-- Neu hinzufügen
```

### Schritt 2: Router einbinden

Füge den Router zur App hinzu:

```python
# Include routers
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(health_router)
app.include_router(activities_router)
app.include_router(meine_routen_router)  # <-- Neu hinzufügen
```

---

## Supabase Client verwenden

Der Supabase Client ist in `services/sabase_client.py` definiert und wird als globale Instanz exportiert:

```python
from services.supabase_client import supabase_client
```

### Daten abfragen (SELECT)

```python
# Einfache Abfrage
daten = await supabase_client.table_select("meine_tabelle")

# Mit Filter
daten = await supabase_client.table_select(
    "meine_tabelle",
    filters={"user_id": "123"}
)

# Bestimmte Spalten
daten = await supabase_client.table_select(
    "meine_tabelle",
    columns="id,name,created_at"
)

# Mit Limit
daten = await supabase_client.table_select(
    "meine_tabelle",
    limit=10
)

# Mit Schema (wichtig für app-Schema!)
daten = await supabase_client.table_select(
    "activities",
    schema="app"  # Verwendet das "app" Schema statt "public"
)
```

### Daten einfügen (INSERT)

```python
# Einzelner Datensatz
result = await supabase_client.table_insert(
    "meine_tabelle",
    {
        "name": "Test",
        "email": "test@example.com"
    }
)

# Mehrere Datensätze
result = await supabase_client.table_insert(
    "meine_tabelle",
    [
        {"name": "Test 1", "email": "test1@example.com"},
        {"name": "Test 2", "email": "test2@example.com"}
    ]
)

# Mit Schema
result = await supabase_client.table_insert(
    "activities_assignments",
    {"user_id": "123", "notes": "Test"},
    schema="app"
)
```

### Daten aktualisieren (UPDATE)

```python
result = await supabase_client.table_update(
    "meine_tabelle",
    {"name": "Neuer Name"},
    filters={"id": "123"}
)
```

### Daten löschen (DELETE)

```python
await supabase_client.table_delete(
    "meine_tabelle",
    filters={"id": "123"}
)
```

### RPC-Funktionen aufrufen

```python
# PostgreSQL-Funktion aufrufen
result = await supabase_client.rpc(
    "meine_funktion",
    params={"param1": "wert1"}
)
```

---

## Neue Funktionalität hinzufügen

### Vollständiges Beispiel: Neue Entität "Projekte"

#### 1. Model erstellen (`models/projekt.py`)

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProjektCreate(BaseModel):
    name: str
    beschreibung: Optional[str] = None

class ProjektResponse(BaseModel):
    id: str
    name: str
    beschreibung: Optional[str]
    user_id: str
    created_at: datetime
```

#### 2. Service erstellen (`services/projekt_service.py`)

```python
"""
Projekt Service
"""
import logging
from typing import Optional
from services.supabase_client import supabase_client

logger = logging.getLogger(__name__)

class ProjektService:
    @staticmethod
    async def create_projekt(user_id: str, name: str, beschreibung: Optional[str] = None):
        """Erstellt ein neues Projekt"""
        return await supabase_client.table_insert(
            "projekte",
            {
                "user_id": user_id,
                "name": name,
                "beschreibung": beschreibung
            },
            schema="app"
        )

    @staticmethod
    async def get_user_projekte(user_id: str):
        """Holt alle Projekte eines Benutzers"""
        return await supabase_client.table_select(
            "projekte",
            filters={"user_id": user_id},
            schema="app"
        )
```

#### 3. Routes erstellen (`api/projekte.py`)

```python
"""
Projekt Routen
"""
import logging
from fastapi import APIRouter, HTTPException, Depends

from models.projekt import ProjektCreate, ProjektResponse
from models.user import TokenMetadata
from services.projekt_service import ProjektService
from services.jwt_service import JwtService
from utils.cookies import get_token_from_cookie

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Projekte"])


async def _get_current_user(token: str | None) -> TokenMetadata:
    from config import settings
    if settings.ENVIRONMENT == "development" and settings.DISABLE_AUTH:
        return TokenMetadata(
            user_id="dev-user",
            email="dev@example.com",
            role="admin",
            person_id=None,
            person_name="Dev User",
        )
    if not token:
        raise HTTPException(status_code=401, detail="Nicht authentifiziert")
    metadata = await JwtService.validate_token(token)
    if not metadata:
        raise HTTPException(status_code=401, detail="Ungültiger Token")
    return metadata


@router.post("/projekte", response_model=ProjektResponse)
async def create_projekt(
    projekt: ProjektCreate,
    token = Depends(get_token_from_cookie)
):
    """Erstellt ein neues Projekt"""
    user = await _get_current_user(token)

    result = await ProjektService.create_projekt(
        user_id=user.user_id,
        name=projekt.name,
        beschreibung=projekt.beschreibung
    )

    return result


@router.get("/projekte")
async def get_projekte(token = Depends(get_token_from_cookie)):
    """Holt alle Projekte des aktuellen Benutzers"""
    user = await _get_current_user(token)
    projekte = await ProjektService.get_user_projekte(user.user_id)
    return {"projekte": projekte}
```

#### 4. Router registrieren (`main.py`)

```python
# Import routers
from api.projekte import router as projekte_router  # <-- Hinzufügen

# Include routers
app.include_router(projekte_router)  # <-- Hinzufügen
```

---

## Best Practices

### 1. Logging verwenden

```python
import logging
logger = logging.getLogger(__name__)

@router.get("/beispiel")
async def beispiel():
    logger.info("Beispiel-Route aufgerufen")
    logger.warning("Etwas könnte schiefgehen")
    logger.error("Ein Fehler ist aufgetreten")
```

### 2. Fehlerbehandlung

```python
@router.get("/daten/{id}")
async def get_daten(id: str, token = Depends(get_token_from_cookie)):
    user = await _get_current_user(token)

    try:
        daten = await supabase_client.table_select(
            "daten",
            filters={"id": id, "user_id": user.user_id}
        )

        if not daten:
            raise HTTPException(status_code=404, detail="Daten nicht gefunden")

        return daten

    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Daten: {e}")
        raise HTTPException(status_code=500, detail="Interner Serverfehler")
```

### 3. Pydantic Models für Validierung

```python
from pydantic import BaseModel, EmailStr, validator
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    age: Optional[int] = None

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Name darf nicht leer sein')
        return v
```

### 4. Schema-Parameter nicht vergessen

Die meisten Tabellen in diesem Projekt befinden sich im `app` Schema:

```python
# FALSCH - sucht in public schema
await supabase_client.table_select("activities")

# RICHTIG - sucht in app schema
await supabase_client.table_select("activities", schema="app")
```

### 5. Async/Await konsistent verwenden

```python
# RICHTIG
@router.get("/daten")
async def get_daten():
    result = await supabase_client.table_select("tabelle")
    return result

# FALSCH - wird Fehler verursachen
@router.get("/daten")
async def get_daten():
    result = supabase_client.table_select("tabelle")  # await fehlt!
    return result
```

---

## Schnellreferenz

| Aktion | Code |
|--------|------|
| Router erstellen | `router = APIRouter(prefix="/api", tags=["Tag"])` |
| Öffentliche Route | `@router.get("/endpoint")` |
| Geschützte Route | `@router.get("/endpoint"), token = Depends(get_token_from_cookie)` |
| Token validieren | `JwtService.validate_token(token)` |
| DB Select | `await supabase_client.table_select("tabelle", schema="app")` |
| DB Insert | `await supabase_client.table_insert("tabelle", {...}, schema="app")` |
| DB Update | `await supabase_client.table_update("tabelle", {...}, filters={...})` |
| DB Delete | `await supabase_client.table_delete("tabelle", filters={...})` |
| RPC aufrufen | `await supabase_client.rpc("funktion", params={...})` |
