## Cursor Cloud specific instructions

### Architecture

Microservice crypto analytics platform: Next.js 14 frontend (port 3000), FastAPI backend (port 8000), FastAPI ML service (port 8001), Celery workers, PostgreSQL, Redis. See `README.md` for details.

### Infrastructure

- PostgreSQL + Redis run via Docker: `sudo docker compose -f docker-compose.simple.yml up -d`
- Backend uses SQLite by default (`USE_SQLITE=true` in `app/core/config.py`). To use Postgres, set `USE_SQLITE=false` and `DATABASE_URL` env var.

### Running services natively (development)

```bash
# Backend (port 8000)
cd backend && source .venv/bin/activate
USE_SQLITE=true SECRET_KEY="dev-key-32chars" python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ML Service (port 8001)
cd ml-service && source .venv/bin/activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001

# Frontend (port 3000)
cd frontend && npm run dev
```

### Gotchas

- **Tailwind CSS**: Project uses Tailwind v3 with `tailwindcss` PostCSS plugin (NOT `@tailwindcss/postcss` which is v4). If `package.json` has v4 dependencies, downgrade to v3.
- **bcrypt**: `passlib[bcrypt]` requires `bcrypt==4.0.1` (not 5.x) to avoid `ValueError` on password hashing.
- **Next.js pages conflict**: Root `pages/` and `src/pages/` both exist. Next.js only serves root `pages/`. See `REVISION_PLAN.md` for details.
- **Frontend npm install**: Requires `--legacy-peer-deps` flag due to `@testing-library/react-hooks` peer dep conflict.
- **Husky pre-commit**: Use `HUSKY=0` to bypass pre-commit hooks when committing (ESLint not installed at root level).

### Lint / Test / Build

- **Frontend lint**: `cd frontend && npx next lint` (requires `eslint@^8`, `eslint-config-prettier`)
- **Frontend tests**: `cd frontend && npx jest --passWithNoTests` (pre-existing failures)
- **Frontend build**: `cd frontend && npx next build` (fails due to pre-existing ESLint errors)
- **Backend tests**: `cd backend && source .venv/bin/activate && python -m pytest tests/ -v` (10 pass, 1 fail, 2 errors — pre-existing)
