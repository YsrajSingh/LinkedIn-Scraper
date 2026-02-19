# LinkedIn Scraping API

FastAPI service that exposes company and profile scrapers as HTTP endpoints.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/company` | Search multiple companies |
| POST | `/profile` | Search multiple profiles |
| GET | `/` | API info |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |

## Request Examples

### POST /company

Search by company handle (e.g. `tutorflo`, `microsoft`) or full URL. No directory required.

```json
{
  "companies": ["tutorflo", "microsoft", "openai"]
}
```

### POST /profile

```json
{
  "profiles": ["satya-nadella", "reidhoffman", "bill-gates"]
}
```

## Run the API

```bash
# From project root, with venv activated
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000/docs for interactive API docs.
