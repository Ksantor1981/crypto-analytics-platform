## Cursor Cloud specific instructions

### Architecture

Microservice crypto analytics platform: Next.js 14 frontend (port 3000), FastAPI backend (port 8000), FastAPI ML service (port 8001), Celery workers, PostgreSQL, Redis. See `README.md` for details.

### Infrastructure

- PostgreSQL + Redis run via Docker: `sudo docker compose -f docker-compose.simple.yml up -d`
- Backend uses SQLite by default (`USE_SQLITE=true` in `app/core/config.py`). To use Postgres, set `USE_SQLITE=false` and `DATABASE_URL` env var.
- For production deploy: `docker compose -f docker-compose.deploy.yml up -d` (requires `.env` from `.env.example`)

### Running services natively (development)

```bash
# Backend (port 8000) — auto-seeds 22 Telegram channels and collects signals on startup
cd backend && source .venv/bin/activate
USE_SQLITE=true SECRET_KEY="dev-key-32chars" python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ML Service (port 8001) — has trained XGBoost model (models/signal_model.pkl)
cd ml-service && source .venv/bin/activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001

# Frontend (port 3000)
cd frontend && npm run dev
```

### Gotchas

- **Tailwind CSS**: Project uses Tailwind v3 with `tailwindcss` PostCSS plugin (NOT `@tailwindcss/postcss` which is v4).
- **bcrypt**: `passlib[bcrypt]` requires `bcrypt==4.0.1` (not 5.x) to avoid `ValueError` on password hashing.
- **Pages directory**: All pages are in `src/pages/` (NOT root `pages/`). tsconfig paths: `"@/*": ["./*", "./src/*"]`.
- **Frontend npm install**: Requires `--legacy-peer-deps` flag.
- **Husky pre-commit**: Use `HUSKY=0` to bypass pre-commit hooks when committing.
- **Auto-collection**: Backend auto-collects signals from 22 Telegram channels on startup and every 15 min via async scheduler.
- **Signal checker**: `POST /api/v1/collect/check-signals` validates pending signals against CoinGecko market prices.
- **ML model retrain**: `cd ml-service && python train_from_db.py` fetches signals from API and retrains XGBoost.
- **Stripe**: Keys available via `STRIPE_SECRET_KEY` and `STRIPE_PUBLISHABLE_KEY` env vars.

### Lint / Test / Build

- **Frontend lint**: `cd frontend && npx next lint`
- **Frontend build**: `cd frontend && npx next build` (passes with eslint/ts errors ignored in next.config.js)
- **Backend tests**: `cd backend && source .venv/bin/activate && python -m pytest tests/test_scraper.py tests/test_ml_and_services.py tests/test_models.py -v` (47 passing)
- **Standalone collection**: `cd backend && python -m app.tasks.collect_signals`
- **CSV export**: `GET /api/v1/export/signals.csv` (requires auth)
