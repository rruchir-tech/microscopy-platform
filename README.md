# 🔬 Microscopy Pipeline Platform

A no-code web platform for building microscopy image-analysis pipelines, running
them over batches of images, and exporting quantitative results — aimed at
biology/microscopy labs.

Researchers drag image-processing modules onto a canvas, connect them into a
pipeline, point a batch job at a folder of images, and download a CSV of
per-cell metrics plus annotated images. No coding required.

---

## Quick start (MicroCount, single server)

The simplest path: one server runs the API **and** serves the built frontend.

```bash
# 1. install deps + build the frontend (writes frontend/dist)
./start.sh build

# 2. run it (http://localhost:8000)
./start.sh                 # or: uvicorn backend.app.main:app --reload
```

Open <http://localhost:8000> and log in with the auto-seeded demo account:

- **Email:** `demo@demo.com`  ·  **Password:** `demo12345`

**The no-code flow ("New Analysis"):** drag-drop a folder of microscopy images →
they're auto-organized by capture date (EXIF, falling back to file date) →
tick what to measure (**cell count**, **fluorescence intensity**) → **Process**.
You get live progress, annotated overlays, and a ZIP with `results.csv`,
`metadata.json` (params + per-image dates for reproducibility), and
`annotated_images/`. No images handy? Hit **Try with demo images**.

For separate dev servers (hot reload), run `uvicorn` in `backend/` and
`npm run dev` in `frontend/` instead.

---

## Features

- **Auth** — JWT access/refresh tokens, bcrypt password hashing.
- **Visual pipeline builder** — node-based editor (React Flow) with a draggable
  module library and per-module parameter panel.
- **8 chainable image-processing modules** — load, preprocess, threshold, cell
  detection, intensity measurement, colocalization, classification, export.
- **Async batch processing** — Celery + Redis, with live progress tracking.
- **Results & export** — sortable result table, histograms/scatter charts
  (Recharts), CSV + ZIP download.
- **Pre-built templates** — Cell Counter, Nuclei Intensity Profiler,
  Two-Channel Colocalization.
- **Runs anywhere** — PostgreSQL + Redis in production; SQLite + eager Celery
  for zero-infra local dev and CI.

---

## Architecture

```
┌────────────┐      REST/JWT      ┌────────────┐      tasks      ┌──────────┐
│  Frontend  │ ─────────────────► │  FastAPI   │ ──────────────► │  Celery  │
│ React + TS │ ◄───────────────── │  backend   │ ◄────────────── │  worker  │
└────────────┘                    └─────┬──────┘   results        └────┬─────┘
                                        │                              │
                                  ┌─────┴──────┐                 ┌─────┴─────┐
                                  │ PostgreSQL │                 │   Redis   │
                                  └────────────┘                 └───────────┘
```

**Backend:** FastAPI · SQLAlchemy 2 · Pydantic v2 · Celery · OpenCV /
scikit-image / NumPy (with pure-NumPy fallbacks) · PyJWT · bcrypt.

**Frontend:** React 18 · TypeScript · Vite · Tailwind · React Flow · React Query
· Zustand · React Hook Form + Zod · Recharts · Axios.

---

## Quick start (Docker)

```bash
cp .env.example .env          # tweak JWT_SECRET etc.
docker-compose up --build
```

- Frontend → http://localhost:5173
- API docs → http://localhost:8000/docs

> Docker brings up PostgreSQL, Redis, the API, a Celery worker, and the
> frontend. (Docker is **not** required for local dev — see below.)

---

## Local development (no Docker)

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   |   *nix: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Defaults to a local **SQLite** database (`data/app.db`) and runs Celery tasks
**eagerly** (inline, no broker) — so the full register → build → run → results
flow works with nothing else installed.

For real async processing, set `CELERY_TASK_ALWAYS_EAGER=false`, point
`DATABASE_URL`/`REDIS_URL` at PostgreSQL/Redis, and start a worker:

```bash
celery -A app.celery_app.celery_app worker --loglevel=info
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

Set `VITE_API_BASE_URL` (default `http://localhost:8000`) in `.env` if needed.

---

## Image-processing modules

| Module | Purpose | Key parameters |
| --- | --- | --- |
| `image_load` | Load & resize | `target_size` |
| `preprocessing` | Blur / normalize / denoise | `blur_kernel`, `normalize`, `denoise_strength` |
| `thresholding` | Binary mask | `method` (otsu/manual/adaptive), `threshold_value` |
| `cell_detection` | Label cells | `model_type`, `diameter` |
| `intensity_measurement` | Per-cell intensity & area | `channel` |
| `colocalization` | Pearson + Manders | `region_size` |
| `classification` | Label cells (heuristic/ML) | `model_type`, `confidence_threshold` |
| `export_results` | CSV (+ annotated images) | `include_images` |

> **CellPose** segmentation is optional. It pulls in PyTorch (multi-GB), so it
> is imported lazily; when absent, `cell_detection` falls back to
> connected-components on the threshold mask. Install with
> `pip install cellpose` to enable learned segmentation.

A pipeline is stored as a `{nodes, edges}` graph:

```json
{
  "nodes": [
    { "id": "n1", "type": "image_load", "params": { "target_size": 512 } },
    { "id": "n2", "type": "cell_detection", "params": { "diameter": 15 } },
    { "id": "n3", "type": "export_results", "params": { "include_images": true } }
  ],
  "edges": [
    { "source": "n1", "target": "n2" },
    { "source": "n2", "target": "n3" }
  ]
}
```

---

## API overview

`/docs` (Swagger) lists everything. Highlights:

| Group | Endpoints |
| --- | --- |
| Auth | `POST /api/auth/register` · `/login` · `/refresh` · `GET /api/auth/me` |
| Pipelines | `GET/POST /api/pipelines` · `GET/PUT/DELETE /api/pipelines/{id}` · `POST .../clone` · `GET /api/pipelines/modules` |
| Jobs | `POST /api/jobs` · `GET /api/jobs` · `GET /api/jobs/{id}` · `/results` · `/results.csv` · `/download` · `POST /api/jobs/{id}/cancel` |
| Templates | `GET /api/templates` · `POST /api/templates/{id}/instantiate` |
| User | `GET /api/user/storage` · `/tier-limits` · `PUT /api/user/settings` |

---

## Testing

```bash
# Backend (SQLite, eager Celery — no external services)
cd backend && pytest -q

# Frontend unit tests
cd frontend && npm run test

# E2E (needs backend + frontend dev server running)
cd frontend && npm run e2e
```

---

## Configuration

All settings come from environment variables — see [`.env.example`](.env.example).
Key ones: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `CELERY_TASK_ALWAYS_EAGER`,
`UPLOAD_FOLDER`, `RESULTS_FOLDER`, `CORS_ORIGINS`, `VITE_API_BASE_URL`.

No secrets are committed; `.env` is git-ignored.

---

## Deployment

Each service ships a Dockerfile; `docker-compose.yml` wires the full stack.
For a managed host (Render, Railway, Fly.io): deploy the backend image with
managed PostgreSQL + Redis add-ons, run the Celery worker as a second service,
and serve the frontend build as a static site (or its nginx image).

GitHub Actions (`.github/workflows/`): `test.yml` (lint + unit tests + build),
`build-images` (Docker build on `main`), `codeql` (security scanning).
