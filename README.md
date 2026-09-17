# مخمخ · Makhmakh AI

منصة تعلّم عربية بالذكاء الاصطناعي: ترفع ملفاتك الدراسية (PDF، عرض تقديمي، صوت، فيديو)،
ومخمخ يستخرج المفاهيم، يبني خريطة تعلّم مرتّبة، ويجاوب على أسئلتك من محتواك أنت وبمصادر.

An Arabic-first learning platform: upload your study material, and Makhmakh extracts the
concepts, orders them into a study path, and answers questions grounded in your own
content with citations.

---

## Monorepo layout

| Path | What it is |
| --- | --- |
| `back/` | FastAPI + SQLAlchemy 2 + Alembic backend (PostgreSQL + pgvector, Redis) |
| `front/` | Next.js 16 App Router frontend (Arabic RTL + English) |
| `docker-compose.yml` | Postgres (pgvector), Redis, API, RQ workers, ARQ cron worker |

---

## Quick start

### Everything in Docker

```bash
docker compose up --build
```

This brings up Postgres (with `pgvector`), Redis, the API on `http://localhost:8000`,
the RQ workers that process uploaded material, and the ARQ worker that runs the
scheduled jobs. Apply migrations once the stack is healthy:

```bash
docker compose exec api alembic upgrade head
```

### Backend manually

```bash
cd back
python -m venv .venv && . .venv/Scripts/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                  # then fill in the secrets
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Queues are optional in development: when Redis is unreachable the API runs the job
in a background thread instead of failing the request, so uploads still get processed.

Worker processes (when Redis is available):

```bash
rq worker material_processing video_generation payment_processing email_delivery \
  --url redis://localhost:6379/0        # content processing
arq arq_worker.WorkerSettings           # scheduled jobs (payments, token cleanup)
```

### Frontend

```bash
cd front
npm install
cp .env.example .env.local
npm run dev        # http://localhost:3000
```

The Arabic UI is served from `/`, English from `/en`.

---

## Configuration

* `back/.env.example` — database, Redis, JWT, SMTP, payment providers, and the AI
  gateway credentials. Gemini keys can be supplied as `GEMINI_API_KEYS` (comma
  separated) or through the individual `GEMINI_API_KEY_DEV` / `GEMINI_API_KEY_PROD_N`
  variables used by the multi-project rotation.
* `front/.env.example` — `NEXT_PUBLIC_API_URL` (backend origin) and
  `NEXT_PUBLIC_SITE_URL` (canonical/OG origin).

The API is versioned under `/api/v1` and its contract is published at
`http://localhost:8000/docs`.

---

## Verification

Frontend:

```bash
cd front
npm run lint          # ESLint (next/core-web-vitals + typescript)
npm run typecheck     # tsc --noEmit, typed translation keys
npm run build         # production build
npm run check:api     # every frontend call vs. the backend OpenAPI routes
```

`npm run check:api` fetches `openapi.json` from a running backend (or takes
`--spec <file>`) and fails if a request path or HTTP method no longer exists.

Backend:

```bash
cd back
pytest app/ai/ai_gateway -q     # AI gateway key rotation, no network calls
alembic upgrade head            # migrations
```

---

## Brand system

Design tokens live in `front/app/globals.css` and the brand palette is the only
palette in the app:

| Token | Value | Use |
| --- | --- | --- |
| `brand-500` | `#FF5900` | primary actions, highlights |
| `cocoa-800` | `#663300` | depth, strong contrast |
| `brand-400` | `#FF8100` | secondary orange |
| `brand-300` | `#FFC200` | accents |
| `brand-100` | `#FFEEA6` | soft highlights |
| `ink` | `#0C0C0C` | text |
| `surface` | `#F4F4F4` | page background |

Typography is intentional and layered (`front/app/fonts.ts`):

* **Thamanya Sans** (`font-sans`) — every UI surface: body copy, navigation, forms, tables.
* **Hayah** (`font-display`) — section titles and prominent headings.
* **Aviny** (`font-brand`) — reserved for a single hero-level brand statement per page.

Logo assets are in `front/public/brand/` and the favicon is `front/app/icon.png`.
