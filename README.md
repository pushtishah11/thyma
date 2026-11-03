# Thyma

[![CI](https://github.com/pushtishah11/thyma/actions/workflows/ci.yml/badge.svg)](https://github.com/pushtishah11/thyma/actions/workflows/ci.yml)

A health record for people with PCOS and thyroid conditions.

Symptoms, irregular cycles, lab results, meds and supplements, and food all live in
one place, and Thyma turns them into a one-page summary a doctor can read in two
minutes. It doesn't assume a 28-day cycle, it doesn't predict fertility, and it
never diagnoses: it only describes what you logged.

> **Status:** early development (milestone M0: project setup).

## Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 16
- **Frontend:** React + TypeScript, Vite
- **Tests and lint:** pytest, ruff, ESLint, GitHub Actions

## Running it locally

You need [Docker](https://www.docker.com/products/docker-desktop/),
Python 3.12 and Node 22.

**1. Start Postgres** (from the repo root)

```bash
docker compose up -d
```

This creates two databases: `thyma` for the app and `thyma_test` for the tests.

**2. Set up and start the backend** (in its own terminal)

```bash
cd backend
python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload --port 8000
```

**3. Set up and start the frontend** (in a second terminal)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The status card should show both the API and the
database as OK.

Settings come from environment variables, and the defaults match
`docker-compose.yml`, so no `.env` file is needed for local development. To
change something, copy `.env.example` to `.env` and add `--env-file ../.env` to
the `uvicorn` command.

## Tests and lint

```bash
cd backend
.venv/bin/ruff check . && .venv/bin/ruff format --check .
.venv/bin/pytest
```

```bash
cd frontend
npm run lint && npm run build
```

The backend tests run against `thyma_test` and rebuild its schema from the
migrations on every run, so they never touch your real data.

## Project layout

```
backend/
  app/          FastAPI app: config, db, models, routers, services
  alembic/      database migrations
  tests/        pytest suite
frontend/
  src/          React app; all API calls go through src/api.ts
docker-compose.yml
```

## Data and privacy

The repo never contains real health data or real lab reports, not even as test
fixtures. Every test and demo dataset is synthetic.
