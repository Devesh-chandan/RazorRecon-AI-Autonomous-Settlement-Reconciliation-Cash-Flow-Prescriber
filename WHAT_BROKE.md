# WHAT BROKE — Real Engineering Failure Recovery Log 🛡️

**Project:** RazorRecon AI — Autonomous Settlement Reconciliation & Cash-Flow Prescriber  
**Track:** Razorpay Buildathon 2026 — Track 04 (AI Finance Controller)  

This is an authentic, unedited engineering log of **33 real failure modes** encountered while building, debugging, and deploying RazorRecon AI. It documents exact error stack traces, root causes, and production fixes across webhooks, database state, reconciliation logic, LLM integration, frontend streaming, and DevOps.

---

## 📊 Summary by Pillar

| Category | Solved Incidents | Focus Area & Architectural Fixes |
|---|:---:|---|
| 🔐 **Webhooks & HMAC Verification** | 4 | HMAC-SHA256 signature verification, Starlette stream double-read, ngrok SSL tunneling |
| 🐘 **Database & Schema Drift** | 4 | Startup schema auto-healing (`auto_heal_schema`), Alembic migration sync, primary key truncation |
| ⚡ **Concurrency & High Load** | 3 | Locust load benchmarking (100–500 users), non-blocking thread pool execution, SSE queue isolation |
| 🧠 **LLM Diagnostics & Prompts** | 3 | Groq Llama 3.3 70B JSON schema validation, bilingual prompt tuning, fallback diagnostic engine |
| 🧮 **Financial Edge Cases & Math** | 4 | UTC/IST date shift, T+1/T+2 settlement windows, MDR fee tolerance (±₹5), GST rounding (₹0.02) |
| 💻 **Environment & Cross-Platform** | 3 | Windows PowerShell Unicode encoding, Docker Compose v2 migration, hardcoded UI data fixes |
| 📥 **CSV Batch Importer** | 4 | Pandas chunking (50MB uploads), deduplication counters, VARCHAR(20) ID slicing |
| 🔴 **Redis Cache & DB State** | 3 | `db.flush()` execution order, UUID string serialization, What-If cache invalidation |
| 🛡️ **Auth, CORS & Security** | 3 | Starlette CORS preflight OPTIONS 200 handler, SlowAPI rate limiting, OAuth2 JWT tokens |
| 🧪 **Test Suite & CI/CD** | 2 | Pytest database pollution isolation, `pytest.ini` pythonpath resolution, static type paths |

---

## 📍 Index of All 33 Incidents

1. [Webhook stream already consumed (`await request.json()`)](#1)
2. [HMAC signature verification failure (401 Unauthorized)](#2)
3. [Webhook returns 200 OK but data doesn't show up after recon](#3)
4. [Razorpay webhook fails against local Nginx over HTTPS](#4)
5. [Production startup crash — `UndefinedColumn: column "gateway" does not exist`](#5)
6. [Pytest fails on a fresh database (`UndefinedTable`)](#6)
7. [Bulk test data loading wiping existing seed records](#7)
8. [CSV import truncation error (`StringDataRightTruncation`)](#8)
9. [Locust load test hitting wrong route (`GET /api/cashflow/forecast`)](#9)
10. [Deprecated `asyncio.get_event_loop()` warning on Python 3.10+](#10)
11. [SSE error handler firing twice on client disconnect](#11)
12. [`hmac.new()` TypeError on every incoming webhook](#12)
13. [SlowAPI rate limiter exception handler signature linter warning](#13)
14. [Pass 4 crash when `GROQ_API_KEY` is missing or rate-limited](#14)
15. [What-If cashflow filter dropping CSV orders with null capture dates](#15)
16. [Cross-midnight 11:50 PM IST order matching failure in Pass 2](#16)
17. [MDR fee tier variance causing false break flags](#17)
18. [GST tax rounding discrepancy producing phantom breaks](#18)
19. [Windows PowerShell Unicode encoding error (`UnicodeEncodeError`)](#19)
20. [Hardcoded 96.0% match rate string on breakdown page](#20)
21. [Obsolete `version` key in docker-compose.yml](#21)
22. [CSV-generated payment IDs truncated incorrectly](#22)
23. [Duplicate CSV rows not counted as skipped](#23)
24. [Large 50MB CSV file import memory spikes](#24)
25. [Redis cache missing `id` and UUID Pydantic validation failure](#25)
26. [What-If simulation failing to invalidate Redis cache](#26)
27. [CORS preflight 400 on OPTIONS requests](#27)
28. [Inconsistent product naming across frontend and backend](#28)
29. [Navbar progress bar cramped against language toggle](#29)
30. [Pytest suite polluting live database with temporary test rows](#30)
31. [`ModuleNotFoundError: No module named 'app'` when running pytest](#31)
32. [IDE static analysis can't resolve `app.database`](#32)
33. [Cron pinger failing on oversized/wrong-method response](#33)

---

<a id="1"></a>
### 1. Webhook stream already consumed (`await request.json()`)

* **What Broke:** Calling `await request.json()` inside `POST /api/webhooks/razorpay` threw a Starlette `RuntimeError: Stream consumed` or returned an empty payload `{}`.
* **Root Cause:** To verify `X-Razorpay-Signature`, the route first called `await request.body()` to read raw payload bytes for HMAC-SHA256 hashing. Starlette request streams can only be read once. When the route later called `request.json()`, the underlying stream buffer was already empty.
* **Fix:** FastAPI automatically parses and injects the request body JSON via `body: dict = Body(...)`. I removed manual `request.json()` calls and used the injected `body` dictionary directly:
  ```python
  @router.post("/razorpay")
  async def handle_razorpay_webhook(
      request: Request,
      body: dict = Body(...),
      db: Session = Depends(get_db)
  ):
      payload: dict = body  # Injected by FastAPI from Body(...)
  ```

---

<a id="2"></a>
### 2. HMAC signature verification failure (401 Unauthorized)

* **What Broke:** Manual test requests sent via Swagger UI or PowerShell were rejected with `HTTP 401 Unauthorized: {"detail": "Invalid X-Razorpay-Signature"}`.
* **Root Cause:** When `RAZORPAY_WEBHOOK_SECRET` is configured in `backend/.env`, `routes/ingestion.py` computes `hmac.new(secret, raw_body, sha256).hexdigest()` and checks it against the `X-Razorpay-Signature` request header. Manual requests lacked a valid signature hash.
* **Fix:**
  1. Wrote a dedicated CLI test tool `python -m app.send_test_webhook` that reads the secret from `.env`, computes the exact HMAC-SHA256 signature, and fires properly signed event pairs.
  2. For local dev without a secret, leaving `RAZORPAY_WEBHOOK_SECRET=` empty in `.env` causes `ingestion.py` to skip verification with a warning log.

---

<a id="3"></a>
### 3. Webhook returns 200 OK but data doesn't show up after recon

* **What Broke:** Sending a single `payment.captured` webhook returned `200 OK`, but running reconciliation showed 0 matched settlements in the workbench.
* **Root Cause:** `payment.captured` inserts a row into the `orders` table. However, the reconciliation engine matches **Order** rows against **Settlement** rows (`settlements`). Without a corresponding `settlement.processed` event, the order remains an open unsettled item.
* **Fix:** Updated test scripts (`send_test_webhook.py`) to emit paired events — first `payment.captured` (creating the Order), followed immediately by `settlement.processed` (creating the Settlement row).

---

<a id="4"></a>
### 4. Razorpay webhook fails against local Nginx over HTTPS

* **What Broke:** Setting the webhook URL in Razorpay Dashboard to `https://localhost/api/webhooks/razorpay` resulted in `Delivery Failed: SSL Certificate Error`.
* **Root Cause:** Local Nginx used a self-signed SSL certificate (`selfsigned.crt`). Razorpay's production servers verify SSL certificates and reject untrusted self-signed handshakes.
* **Fix:** Tunnelled traffic directly to FastAPI using ngrok:
  ```bash
  ngrok http 8000
  ```
  Ngrok provides a valid CA-signed HTTPS endpoint (`*.ngrok-free.dev`) accepted by Razorpay.

---

<a id="5"></a>
### 5. Production startup crash — `UndefinedColumn: column "gateway" does not exist`

* **What Broke:** Deploying to production failed during app startup with `psycopg2.errors.UndefinedColumn: column "gateway" of relation "settlements" does not exist`.
* **Root Cause:** SQLAlchemy's `Base.metadata.create_all(bind=engine)` creates missing tables, but it does NOT execute `ALTER TABLE` to add new columns to existing tables when ORM models are updated after initial setup.
* **Fix:** Wrote an explicit schema inspector function `auto_heal_schema(db_engine)` in `database.py` using SQLAlchemy `inspect()`. It checks table columns on app startup and executes dynamic `ALTER TABLE` queries if missing:
  ```python
  def auto_heal_schema(engine):
      inspector = inspect(engine)
      columns = [c['name'] for c in inspector.get_columns('settlements')]
      with engine.begin() as conn:
          if 'gateway' not in columns:
              conn.execute(text("ALTER TABLE settlements ADD COLUMN gateway VARCHAR(50)"))
          if 'import_source' not in columns:
              conn.execute(text("ALTER TABLE settlements ADD COLUMN import_source VARCHAR(20) DEFAULT 'seeded'"))
  ```
  Wired `auto_heal_schema(engine)` into FastAPI `lifespan` startup and `seed.py`.

---

<a id="6"></a>
### 6. Pytest fails on a fresh database (`UndefinedTable`)

* **What Broke:** Running pytest against a clean, unseeded database failed 5 tests with `relation "orders" does not exist`.
* **Root Cause:** Table creation (`create_all()`) was previously only called inside `seed.py`, so un-seeded test databases lacked table definitions.
* **Fix:** Added a session-scoped `autouse=True` fixture `setup_test_database()` in `tests/conftest.py` that executes `Base.metadata.create_all(bind=engine)` before any test executes.

---

<a id="7"></a>
### 7. Bulk test data loading wiping existing seed records

* **What Broke:** Running `python -m app.seed` wiped custom imported CSVs and existing database records completely.
* **Root Cause:** `seed.py` performed destructive `db.query(...).delete()` operations on startup.
* **Fix:** Split dataset tools into three distinct scripts:
  * `python -m app.seed`: Sets clean 100-record benchmark dataset.
  * `python -m app.seed_append 50`: Appends 50 new records without wiping existing data.
  * `python -m app.reset`: Completely resets database to 0 records.

---

<a id="8"></a>
### 8. CSV import truncation error (`StringDataRightTruncation`)

* **What Broke:** Importing CSV files threw `psycopg2.errors.StringDataRightTruncation: value too long for type character varying(20)`.
* **Root Cause:** Generated `payment_id` strings like `f"pay_{order_id}"` exceeded the `VARCHAR(20)` column limit when `order_id` was longer than 16 characters.
* **Fix:** Enforced string slicing `[:20]` on all generated primary/foreign keys in `ingestion.py`.

---

<a id="9"></a>
### 9. Locust load test hitting wrong route (`GET /api/cashflow/forecast`)

* **What Broke:** Locust concurrency benchmark reported 100% 404 errors on the cashflow endpoint.
* **Root Cause:** `tests/locustfile.py` requested `GET /api/cashflow/forecast`, but the actual route was `/api/cashflow/{run_id}`.
* **Fix:** Updated `locustfile.py` to store `run_id` upon triggering reconciliation and call `GET /api/cashflow/{self.run_id}` with safety guards.

---

<a id="10"></a>
### 10. Deprecated `asyncio.get_event_loop()` warning on Python 3.10+

* **What Broke:** Executing Pass 4 LLM diagnostics triggered `DeprecationWarning: There is no current event loop` inside thread pool executors.
* **Root Cause:** `asyncio.get_event_loop()` is deprecated in modern Python when called outside the main event loop thread.
* **Fix:** Replaced with `asyncio.get_running_loop()` inside `reconcile.py`:
  ```python
  loop = asyncio.get_running_loop()
  p4_results = await loop.run_in_executor(None, run_pass4, p3["breaks"])
  ```

---

<a id="11"></a>
### 11. SSE error handler firing twice on client disconnect

* **What Broke:** Network disconnects during live progress streaming logged duplicate `RECON_ERROR` events and threw errors from calling `.close()` on a closed `EventSource`.
* **Root Cause:** Both `es.addEventListener('error', ...)` and `es.onerror` were registered in `client.js` and fired on the same disconnect event.
* **Fix:** Added a single named error handler with a boolean guard flag (`errorFired`):
  ```javascript
  let errorFired = false;
  const handleSseError = (data) => {
    if (errorFired) return;
    errorFired = true;
    onEvent({ event: 'error', data });
    es.close();
  };
  ```

---

<a id="12"></a>
### 12. `hmac.new()` TypeError on every incoming webhook

* **What Broke:** Every incoming webhook crashed with `TypeError: new() got an unexpected keyword argument 'key'`.
* **Root Cause:** CPython's `hmac.new(key, msg, digestmod)` requires positional arguments, but code passed keyword arguments `hmac.new(key=...)`.
* **Fix:** Fixed parameter syntax to positional format: `hmac.new(secret.encode('utf-8'), raw_body, hashlib.sha256).hexdigest()`.

---

<a id="13"></a>
### 13. SlowAPI rate limiter exception handler signature linter warning

* **What Broke:** Pyrefly flagged `app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)` with `bad-argument-type`.
* **Root Cause:** Starlette's handler signature expects `(Request, Exception) -> Response`, while SlowAPI's internal handler is typed as `(Request, RateLimitExceeded) -> Response`.
* **Fix:** Added a custom wrapper function `rate_limit_handler(request: Request, exc: Exception)` in `main.py` to satisfy contravariance checks while delegating to SlowAPI.

---

<a id="14"></a>
### 14. Pass 4 crash when `GROQ_API_KEY` is missing or rate-limited

* **What Broke:** Running Pass 4 without `GROQ_API_KEY` configured in `.env` caused reconciliation to fail completely.
* **Root Cause:** Groq client initialization threw an uncaught exception when `GROQ_API_KEY` was missing.
* **Fix:** Built `_fallback_diagnostic(break_item)` in `groq_client.py`. If Groq is unavailable, it evaluates heuristic patterns (e.g. `missing_erp_entry`, `data_entry_error`, `chargeback`) and returns structured diagnostics with `confidence = 0.88`, ensuring zero pipeline downtime.

---

<a id="15"></a>
### 15. What-If cashflow filter dropping CSV orders with null capture dates

* **What Broke:** `POST /api/cashflow/whatif` failed to include CSV-imported orders when simulating break resolution.
* **Root Cause:** `cashflow.py` filtered on `Order.captured_at.isnot(None)`, but CSV imports only populated `settled_at`.
* **Fix:** Dropped the `captured_at.isnot(None)` filter, allowing both captured and partial-refund orders to participate in 7-day liquidity forecasts.

---

<a id="16"></a>
### 16. Cross-midnight 11:50 PM IST order matching failure in Pass 2

* **What Broke:** Orders placed at 11:50 PM IST were settled on T+1 in IST, but UTC timestamps showed a 2-day date difference, causing false break flags.
* **Root Cause:** Native UTC date comparison ignored the +5:30 IST calendar shift.
* **Fix:** Built `_to_ist_date(dt)` in `pass2_rules.py` to convert timestamps to IST calendar dates before evaluating T+1/T+2 settlement windows.

---

<a id="17"></a>
### 17. MDR fee tier variance causing false break flags

* **What Broke:** Credit card orders with tiered MDR fees (2.0% vs 1.8%) were flagged as breaks.
* **Root Cause:** Pass 1 deterministic matching required exact fee equality.
* **Fix:** Built Pass 2 Rule 2B with `MDR_FEE_TOLERANCE = ±₹5.00` to absorb minor gateway fee tier variances automatically.

---

<a id="18"></a>
### 18. GST tax rounding discrepancy producing phantom breaks

* **What Broke:** Settlements with a ₹0.01 GST tax rounding variance failed deterministic matching.
* **Root Cause:** Floating-point division in GST calculation produced minor rounding deltas.
* **Fix:** Enforced `Decimal.quantize(Decimal("0.01"))` rounding and added `GST_ROUNDING_TOLERANCE = ±₹0.02` in Pass 2 Rule 2D.

---

<a id="19"></a>
### 19. Windows PowerShell Unicode encoding error (`UnicodeEncodeError`)

* **What Broke:** Running python scripts in Windows PowerShell crashed with `UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f680'`.
* **Root Cause:** Default Windows console code page (cp1252) cannot render emoji characters in `print()`.
* **Fix:** Replaced raw emoji in CLI log outputs with plain ASCII markers (`[+]`, `[OK]`, `[WARN]`, `[ERROR]`).

---

<a id="20"></a>
### 20. Hardcoded 96.0% match rate string on breakdown page

* **What Broke:** The Reconciliation Breakdown UI always displayed `96.0% Match Accuracy`, ignoring actual run stats.
* **Root Cause:** `ReconBreakdownFullView.jsx` contained a hardcoded static string `96.0%`.
* **Fix:** Connected component to context stats: `{stats?.match_rate != null ? `${Number(stats.match_rate).toFixed(1)}%` : '—'}`.

---

<a id="21"></a>
### 21. Obsolete `version` key in docker-compose.yml

* **What Broke:** `docker compose up` printed `the attribute 'version' is obsolete, it will be ignored` on every execution.
* **Root Cause:** Docker Compose v2 deprecated top-level `version: "3.9"` attribute.
* **Fix:** Removed `version: "3.9"` from `docker-compose.yml` and `docker-compose.prod.yml`.

---

<a id="22"></a>
### 22. CSV-generated payment IDs truncated incorrectly

* **What Broke:** Settlement CSV imports produced `payment_id` values that mismatched order records, breaking Pass 1 matching.
* **Root Cause:** `payment_id` was built as `(entity_id or f"pay_{order_id}")[:20]`. When `entity_id` was missing, long order IDs caused invalid slicing.
* **Fix:** Refactored ID extraction in `ingestion.py`:
  ```python
  entity_id_raw = str(data.get("entity_id", "") or "").strip()
  payment_id = (entity_id_raw if entity_id_raw else f"pay_{order_id}")[:20]
  ```

---

<a id="23"></a>
### 23. Duplicate CSV rows not counted as skipped

* **What Broke:** Re-importing a settlement CSV returned `rows_skipped == 0` instead of skipping duplicate records.
* **Root Cause:** In `_import_settlements` (`ingestion.py`), existing settlement rows incremented `imported` counter instead of `skipped`.
* **Fix:** Corrected counter logic to increment `skipped += 1` and `continue` when duplicate `settlement_id` is found.

---

<a id="24"></a>
### 24. Large 50MB CSV file import memory spikes

* **What Broke:** Uploading 50MB settlement files caused high memory consumption.
* **Root Cause:** Reading full file into memory at once using `file.file.read()`.
* **Fix:** Streamed CSV parsing using Pandas `chunksize` batching in `ingestion.py`.

---

<a id="25"></a>
### 25. Redis cache missing `id` and UUID Pydantic validation failure

* **What Broke:** Fetching cached reconciliation results from Redis caused React `key` prop warnings and Pydantic `ValidationError`.
* **Root Cause:** 
  1. `cache_results` was invoked before `db.flush()`, so `ReconResult.id` was `None`.
  2. `run_id` was passed as a raw Python `UUID` object instead of a string.
* **Fix:** Added `db.flush()` before caching and explicitly cast `"run_id": str(r.run_id)` and `"id": r.id`.

---

<a id="26"></a>
### 26. What-If simulation failing to invalidate Redis cache

* **What Broke:** Resolving a break in What-If simulation did not update cached cash-flow projection curves.
* **Root Cause:** Redis key `razorrecon:cashflow:<run_id>` was not invalidated when `POST /api/cashflow/whatif` was called.
* **Fix:** Added explicit cache invalidation `redis_client.delete(f"razorrecon:cashflow:{run_id}")` upon resolving a break.

---

<a id="27"></a>
### 27. CORS preflight 400 on OPTIONS requests

* **What Broke:** Frontend POST requests to `/api/recon/run` failed with `OPTIONS 400 Bad Request`.
* **Root Cause:** `SlowAPIMiddleware` intercepted `OPTIONS` preflight requests before `CORSMiddleware` could send CORS headers.
* **Fix:** Implemented custom middleware in `main.py` to intercept `OPTIONS` requests and return `200 OK` with CORS headers immediately.

---

<a id="28"></a>
### 28. Inconsistent product naming across frontend and backend

* **What Broke:** Product title appeared as `RazorRecon & Flow`, `RazorRecon AI`, and `razorrecon-ai`.
* **Root Cause:** Legacy labels from early prototypes.
* **Fix:** Standardized user-facing branding to **RazorRecon** across frontend, backend, docs, and OpenAPI specifications.

---

<a id="29"></a>
### 29. Navbar progress bar cramped against language toggle

* **What Broke:** Live reconciliation progress text was cramped in the top navbar.
* **Root Cause:** Progress element was placed inside the header flex row.
* **Fix:** Moved progress bar to a full-width banner (`.header-progress-banner`) below the top navigation bar.

---

<a id="30"></a>
### 30. Pytest suite polluting live database with temporary test rows

* **What Broke:** Running `pytest tests/test_csv_importer.py` left temporary test rows in the primary database.
* **Root Cause:** Test runner shared the development database session.
* **Fix:** Added an `autouse=True` fixture in `test_csv_importer.py` to delete test records (`setl_u_*`) automatically after each test.

---

<a id="31"></a>
### 31. `ModuleNotFoundError: No module named 'app'` when running pytest

* **What Broke:** Running pytest from repository root threw `ModuleNotFoundError: No module named 'app'`.
* **Root Cause:** `backend/` directory was not included in Python's `sys.path`.
* **Fix:** Configured `pythonpath = backend` in `pytest.ini` and added `sys.path.insert(0, 'backend')` in `tests/conftest.py`.

---

<a id="32"></a>
### 32. IDE static analysis can't resolve `app.database`

* **What Broke:** Pyright/Pylance flagged `Cannot find module app.database`.
* **Root Cause:** Static type checkers resolve paths before runtime `sys.path` changes execute.
* **Fix:** Created `pyrightconfig.json` and `pyproject.toml` with `extraPaths = ["backend"]`.

---

<a id="33"></a>
### 33. Cron pinger failing on oversized/wrong-method response

* **What Broke:** External cron trigger services (e.g. `cron-job.org`) failed on `/api/recon/cron` with `Output too large`.
* **Root Cause:** Endpoint accepted `POST` only, causing `GET` requests from cron providers to fail with HTML 405 error pages (>10KB).
* **Fix:** Converted route to `@router.api_route("/cron", methods=["GET", "POST", "HEAD"])`, returning a lightweight HTTP 200 JSON payload (~75 bytes) while delegating reconciliation to `BackgroundTasks`.
