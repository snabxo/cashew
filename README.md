# Cashew

Cashew is a backend authentication service built with FastAPI, PostgreSQL, SQLAlchemy, and Alembic.

## Project Structure

```
cashew/
├── README.md
├── LICENSE.md
├── docker-compose.yml          # Root stack: backend + postgres
└── backend/
    ├── Dockerfile              # Backend image
    ├── .env.example
    ├── requirements.txt
    ├── cashew.py
    ├── config.py
    ├── database.py
    ├── models.py
    ├── alembic.ini
    ├── alembic/
    │   └── versions/
    └── docker-compose.yml      # Optional: postgres only
```

## Quick Start (Local Development)

1. Create and activate a virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies.

```bash
pip install -r backend/requirements.txt
```

3. Create backend environment file.

```bash
cp backend/.env.example backend/.env
```

4. Start PostgreSQL.

```bash
docker compose up -d cashew-db
```

5. Run migrations.

```bash
alembic -c backend/alembic.ini upgrade head
```

6. Start the API.

```bash
uvicorn backend.cashew:app --reload
```

API docs: `http://localhost:8000/docs`

## Docker Run (Backend + Postgres)

Build and run the full stack from the repository root:

```bash
docker compose up --build
```

Stop and remove containers:

```bash
docker compose down
```

Stop and remove containers plus database volume:

```bash
docker compose down -v
```

## Database Migrations

Create a new migration:

```bash
alembic -c backend/alembic.ini revision --autogenerate -m "your-change"
```

Apply migrations:

```bash
alembic -c backend/alembic.ini upgrade head
```

Rollback one migration:

```bash
alembic -c backend/alembic.ini downgrade -1
```

## License

MIT. See `LICENSE.md`.
