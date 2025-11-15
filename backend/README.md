# Roanes Kitchen Backend

FastAPI backend for the Roanes Kitchen meal planning application.

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development without Docker)

## Quick Start with Docker

1. **Start the services:**
   ```bash
   docker compose up -d --build
   ```

2. **Verify services are running:**
   ```bash
   docker compose ps
   ```

3. **Check the health endpoint:**
   ```bash
   curl http://localhost:8000/health
   ```

   Expected response:
   ```json
   {
     "status": "healthy",
     "app": "Roanes Kitchen",
     "environment": "development"
   }
   ```

4. **View API documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

5. **View logs:**
   ```bash
   docker compose logs -f backend
   ```

6. **Stop services:**
   ```bash
   docker compose down
   ```

## Local Development (without Docker)

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your local PostgreSQL credentials
   ```

4. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

5. **Start the development server:**
   ```bash
   uvicorn app.main:app --reload
   ```

## Database Migrations

### Create a new migration

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations

```bash
alembic upgrade head
```

### Rollback migration

```bash
alembic downgrade -1
```

## Project Structure

```
backend/
├── alembic/              # Database migrations
│   ├── versions/         # Migration files
│   └── env.py           # Alembic configuration
├── app/
│   ├── api/             # API routes
│   ├── core/            # Config and dependencies
│   ├── db/              # Database setup
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   └── main.py          # FastAPI application entry point
├── tests/               # Test files
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker image definition
└── alembic.ini         # Alembic configuration
```

## Testing

```bash
pytest
```

With coverage:
```bash
pytest --cov=app --cov-report=html
```

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key (change in production!)
- `DEBUG`: Enable debug mode
- `ENVIRONMENT`: deployment environment (development/production)
