# T2L Backend Dokumentation

Diese Dokumentation bietet eine Übersicht über die Entwicklung im Time2Log Backend.

## verfügbare Dokumente

| Dokument | Beschreibung |
|----------|--------------|
| [routen-und-services.md](./routen-und-services.md) | Anleitung zum Erstellen von Routen, Verwendung des Supabase Clients und Hinzufügen neuer Funktionalität |

## Schnellstart

### Server starten
```bash
uvicorn main:app --reload
```

### API Dokumentation öffnen
Nach dem Start des Servers ist die interaktive API-Dokumentation verfügbar unter:
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

### Tests ausführen
```bash
pytest
```

## Projektstruktur

```
T2L-Backend-LESV/
├── api/              # API-Routen
├── config/           # Konfiguration & Settings
├── docs/             # Dokumentation
├── models/           # Pydantic Models
├── scripts/          # Hilfsskripte
├── services/         # Business-Logik
├── tests/            # Tests
├── utils/            # Hilfsfunktionen
├── main.py           # App-Einstiegspunkt
└── requirements.txt  # Dependencies
```

## Wichtige Hinweise

1. **Schema-Parameter**: Die meisten Tabellen verwenden das `app` Schema, nicht `public`. Bei Datenbankoperationen `schema="app"` angeben.

2. **Supabase Client**: Dieses Projekt verwendet einen eigenen HTTP-Client statt des offiziellen `supabase` Packages.

3. **Router registrieren**: Neue Router müssen in `main.py` importiert und mit `app.include_router()` registriert werden.
