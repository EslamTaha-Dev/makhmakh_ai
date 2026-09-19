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
| `docker-compose.yml` | Frontend, Postgres (pgvector), Redis, API, and focused RQ workers |

---

## Quick start

### Everything in Docker

```bash
cp .env.example .env   # then fill in the secrets
docker compose up --build
```

Compose loads the shared `.env` from the repository root. It supplies backend
runtime settings and the frontend's `NEXT_PUBLIC_*` build settings.

This brings up the frontend on `http://localhost:3000`, Postgres (with `pgvector`),
Redis, the API on `http://localhost:8000`, the workers that process uploaded
material. Video generation is optional because its local speech stack is large; enable
it with `docker compose --profile media up --build`. Before the API and workers
start, the one-shot `migrate` service applies all Alembic migrations and seeds the
canonical roles, including the default `student` role.

### Backend manually

```bash
cp .env.example .env                                  # from the repository root
cd back
python -m venv .venv && . .venv/Scripts/activate      # Windows: .venv\Scripts\activate
pip install uv
uv pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

For an API-only environment, install `requirements.txt`. Material processing,
video generation, local embeddings, and test tooling have separate requirement
files so production images only carry the features they run. Remote embeddings
use a separately configured OpenAI-compatible endpoint; local embeddings require
`requirements-local-embeddings.txt` and
`EMBEDDING_PROVIDER=sentence-transformers`.

Queues are optional in development when `RUN_JOBS_INLINE=true`; otherwise queue
connection failures are returned instead of attempting heavy worker jobs in the
lightweight API process.

Worker processes (when Redis is available):

```bash
rq worker material_processing --url redis://localhost:6379/0
```

### Frontend

```bash
cd front
npm install
npm run dev        # http://localhost:3000
```

The frontend loads the repository-root `.env`; no second frontend environment
file is needed. The Arabic UI is served from `/`, English from `/en`.

---

## Configuration

Copy the root `.env.example` to `.env`. It contains the database, Redis, JWT,
identity, AI gateway, and frontend settings. Set `LLM_BASE_URL`, `LLM_API_KEY`,
`LLM_MODEL`, and `LLM_MAX_TOKENS` for any OpenAI-compatible Chat Completions
endpoint. The token limit defaults to `4096`, avoiding unexpectedly large and
expensive completion allowances. OpenRouter uses `https://openrouter.ai/api/v1`; OmniRouter uses
`https://omnirouter.li/v1`. Only variables prefixed with `NEXT_PUBLIC_` are
exposed to browser code; never put secrets in those variables.

Embeddings have independent `EMBEDDING_BASE_URL`, `EMBEDDING_API_KEY`, and
`EMBEDDING_MODEL` settings. The configured endpoint must support the OpenAI
Embeddings API and 384-dimensional output. Changing the embedding model causes
stored content to be regenerated for the new model.

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
pytest tests -q                 # AI gateway and backend tests, no AI network calls
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
