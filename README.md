<!-- PROJECT LOGO -->
<div align="center">
  <a href="https://github.com/Devesh-chandan/RazorRecon-AI-Autonomous-Settlement-Reconciliation-Cash-Flow-Prescriber">
    <img src="docs/images/03-dashboard-overview-results.png" alt="RazorRecon — Dashboard showing reconciliation results, 7-day cash flow chart, and settlement workbench">
  </a>

  <h1 align="center">RazorRecon ⚡</h1>

  <p>
    <strong>LLM-Powered Autonomous Settlement Reconciliation & Cash-Flow Prescriber</strong>
    <br />
    Ingest live Razorpay webhooks and bulk settlement CSVs. Reconcile net bank payouts against internal ERP ledgers using a 4-pass hybrid engine. Diagnose complex breaks in English & Hinglish with Llama 3.3 70B. Project 7-day forward cash flow with real-time "What-If" simulations.
    <br />
    <br />
    <a href="https://razor-recon-ai-autonomous-settlemen.vercel.app/" target="_blank"><strong>🌐 Live Demo</strong></a>
    ·
    <a href="#-see-razorrecon-in-action"><strong>See it in action ↓</strong></a>
    ·
    <a href="#-step-by-step-execution-guide"><strong>Get started</strong></a>
    ·
    <a href="http://localhost:8000/docs"><strong>API Docs</strong></a>
    ·
    <a href="PROBLEMS_AND_SOLUTIONS.md"><strong>Troubleshooting</strong></a>
  </p>
</div>

<p align="center">
  <a href="https://razor-recon-ai-autonomous-settlemen.vercel.app/" target="_blank"><img src="https://img.shields.io/badge/Live_Demo-Vercel-000000?style=flat-square&logo=vercel&logoColor=white" alt="Live Demo on Vercel"></a>
  <a href="https://github.com/Devesh-chandan/RazorRecon-AI-Autonomous-Settlement-Reconciliation-Cash-Flow-Prescriber"><img src="https://img.shields.io/badge/Hackathon-Razorpay_Buildathon_2026-0467DF?style=flat-square" alt="Razorpay Buildathon 2026"></a>
  <a href="https://github.com/Devesh-chandan/RazorRecon-AI-Autonomous-Settlement-Reconciliation-Cash-Flow-Prescriber"><img src="https://img.shields.io/badge/Track-04_AI_Finance_Controller-F05032?style=flat-square" alt="Track 04"></a>
  <a href="https://github.com/Devesh-chandan/RazorRecon-AI-Autonomous-Settlement-Reconciliation-Cash-Flow-Prescriber/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/Devesh-chandan/RazorRecon-AI-Autonomous-Settlement-Reconciliation-Cash-Flow-Prescriber/ci.yml?branch=main&style=flat-square&label=build%20%26%20tests" alt="CI Status"></a>
  <a href="https://github.com/Devesh-chandan/RazorRecon-AI-Autonomous-Settlement-Reconciliation-Cash-Flow-Prescriber/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="MIT License"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/LLM-Llama_3.3_70B-0467DF?style=flat-square&logo=meta&logoColor=white" alt="Llama 3.3 70B">
  <img src="https://img.shields.io/badge/Inference-Groq_Cloud-F05032?style=flat-square&logo=speedtest&logoColor=white" alt="Groq Cloud">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.12">
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React 19">
  <img src="https://img.shields.io/badge/Vite-6-646CFF?style=flat-square&logo=vite&logoColor=white" alt="Vite 6">
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL 16">
  <img src="https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white" alt="Redis 7">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker Compose">
</p>

---

## What is RazorRecon?

Razorpay merchants receive daily **net settlements** that lump captured orders, MDR gateway fees, 18% GST on MDR, refunds, and chargebacks into single bulk bank credits. Matching these net payout rows against internal ERP order books across T+1/T+2 settlement cycles is:

| Problem | Impact |
|---|---|
| **⏳ Time-Intensive** | Mid-sized merchants spend 20–40 hours per week manually auditing spreadsheets |
| **⚠️ Error-Prone** | Human error leads to unrecorded breaks, missed tax deductions, and duplicate ledger entries |
| **🌫️ Cash Opaque** | Unresolved breaks obscure usable operating capital and forward liquidity |

**RazorRecon** is an autonomous AI financial controller that solves this end-to-end — from raw webhook events and CSV uploads through 4-pass reconciliation to AI-powered diagnostics and 7-day forward cash flow projection.

---

## ✨ See RazorRecon in action

### 1. Dashboard Initial Idle State
The main workbench initializes in a clean state with metric place-holders and 4-pass pipeline cards ready for execution.

<p align="center">
  <img src="docs/images/01-dashboard-idle.png" alt="RazorRecon dashboard initial idle state showing 4-pass pipeline architecture cards">
</p>

### 2. Real-Time 4-Pass Engine Execution
Triggering reconciliation initiates real-time SSE streaming. Progress bars and skeleton loaders reflect live status pass by pass.

<p align="center">
  <img src="docs/images/02-engine-running-skeleton.png" alt="4-Pass reconciliation engine active streaming state with live skeleton loaders">
</p>

### 3. Reconciliation Overview & Results Workbench
Completed audit displays key financial metrics: 7-Day Confirmed Inflow (₹11.44L), Disputed Exceptions (₹83.89K), 83.0% Recon Rate, and Projected AI Recovery Gain (₹71.30K).

<p align="center">
  <img src="docs/images/03-dashboard-overview-results.png" alt="RazorRecon complete dashboard showing overview KPIs, 7-day cash flow chart, settlement workbench table, and gateway distribution">
</p>

### 4. Merchant Profile & Language Settings Menu
Integrated user menu displaying active Merchant ID (`MID4823099`), language switcher (`EN` / `HI`), Test Mode indicator, and direct API documentation link.

<p align="center">
  <img src="docs/images/04-user-profile-menu.png" alt="Top navigation user profile menu dropdown with Merchant profile and Hinglish language toggle">
</p>

### 5. CSV & Excel Batch Data Import Modal
Drag-and-drop ingestion interface supporting official Razorpay Settlement Reports and Tally/Zoho Books ERP sales ledgers (`.csv` and `.xlsx` files up to 50 MB).

<p align="center">
  <img src="docs/images/05-csv-import-modal.png" alt="Import Batch Data modal with data source type radio buttons and drag-and-drop upload zone">
</p>

### 6. CSV Batch Import Completion Summary
Post-import summary showing rows read, records imported vs duplicate rows skipped, with instant "Audit All DB Records" or "Audit Imported Data Only" action triggers.

<p align="center">
  <img src="docs/images/06-csv-import-success.png" alt="Import Completed Successfully modal showing 50 rows read, 0 imported, 50 skipped duplicates summary">
</p>

### 7. 7-Day Cash Flow Projection & Recovery Analysis Page
Dedicated liquidity forecast page projecting 7-day cash inflow trends, gateway holdback risks, and daily liquidity breakdown tables.

<p align="center">
  <img src="docs/images/07-cashflow-forecast-page.png" alt="7-Day Cash Flow Projection & Recovery Analysis view with trend chart and daily liquidity table">
</p>

### 8. Interactive Cash Flow Chart Tooltip Detail
Hovering over forecast date nodes displays exact confirmed inflow vs disputed exception holdbacks.

<p align="center">
  <img src="docs/images/08-cashflow-chart-tooltip.png" alt="Interactive chart tooltip showing Aug 05 confirmed inflow ₹3.5L vs disputed ₹11.8k">
</p>

### 9. Reconciliation Breakdown — Gateway Performance Matrix
Volume allocation breakdown across payment gateways (HDFC Bank PG 43.8%, Razorpay Stack 23.1%, ICICI Direct 20.3%, Axis UPI Express 11.2%, PhonePe 1.5%).

<p align="center">
  <img src="docs/images/09-recon-breakdown-gateways.png" alt="Reconciliation Breakdown Analysis page showing Gateway Volume Allocation donut chart and performance matrix">
</p>

### 10. Reconciliation Breakdown — Exception Root Cause Actions
Breakdown tab isolating exception root causes with financial impact deltas, priority badges, and actionable next steps.

<p align="center">
  <img src="docs/images/10-recon-breakdown-exceptions.png" alt="Exception Root Cause Actions breakdown showing Unknown and Missing ERP Entry severity cards">
</p>

### 11. AI Exception Analysis & Diagnostics Drawer (English Mode)
Side drawer detailing all unresolved exceptions with LLM confidence scores, root cause explanations, and one-click `Resolve` / `Escalate` actions.

<p align="center">
  <img src="docs/images/11-ai-exception-drawer-en.png" alt="AI Exception Analysis & Diagnostics drawer listing unresolved exception breaks in English">
</p>

### 12. Resolved Exception State via What-If Simulation Engine
Resolving a break updates exception status to `Resolved (What-If Applied)` with a green confirmation badge.

<p align="center">
  <img src="docs/images/12-ai-exception-drawer-resolved.png" alt="AI Exception drawer showing resolved exception item with green confirmation badge">
</p>

### 13. Audit Trail & Execution Log
Comprehensive log of all audit records filterable by Recon Pass (Pass 1–4) and Status (`matched` / `break`) with JSON export capability.

<p align="center">
  <img src="docs/images/13-audit-trail-drawer.png" alt="Audit Trail & Execution Log drawer displaying 101 total entries with pass badges and confidence scores">
</p>

### 14. Detailed Match Audit — Pass 1 Exact Deterministic Match
Expanding a matched row reveals execution context: Recon Pass 1, Deterministic Hash strategy, and matching Order & Settlement IDs.

<p align="center">
  <img src="docs/images/14-matched-row-expanded.png" alt="Expanded workbench row showing Pass 1 Exact Match execution details">
</p>

### 15. What-If Scenario Simulation Curve
Simulating AI exception recovery overlays a blue dashed "What-If" curve on the cash flow chart showing liquidity recovery potential (+₹3.2K).

<p align="center">
  <img src="docs/images/15-whatif-scenario-curve.png" alt="Dashboard showing What-If blue simulation curve overlay on 7-Day Cash Flow chart">
</p>

### 16. AI Exception Audit Detail — Pass 4 AI Diagnosed Break
Expanding a break exception displays LLM diagnosis execution context, confidence rating, root cause alert, and "View AI Analysis →" CTA.

<p align="center">
  <img src="docs/images/16-break-row-expanded.png" alt="Expanded row displaying Pass 4 AI Diagnosed break with root cause alert card">
</p>

### 17. Bilingual AI Diagnostics — Hinglish vs English Comparison
Toggle language mode to view AI diagnostics in natural Hinglish (*"Order order_TH26080055 ka break automatically classify nahi ho saka. Manual review zarori hai."*) or English.

<details>
<summary><strong>🔍 Hinglish vs English — AI Diagnosis Detail Comparison</strong></summary>
<br>

| English Mode | Hinglish Mode |
|---|---|
| <img src="docs/images/18-english-ai-detail-en.png" alt="English AI diagnosis detail" width="400"> | <img src="docs/images/17-hinglish-ai-detail-hi.png" alt="Hinglish AI diagnosis detail" width="400"> |

</details>

---

## 🏗️ How RazorRecon fits into your stack

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRODUCTION CLOUD PIPELINE                         │
│                                                                             │
│ ┌──────────────────────┐      ┌──────────────────┐      ┌─────────────────┐ │
│ │ Vercel / Cloudflare  │ ---> │ AWS ECS / Render │ ---> │ AWS RDS Postgres│ │
│ │ React 19 Frontend    │      │ Gunicorn FastAPI │      │ SSL Managed DB  │ │
│ └──────────────────────┘      └────────┬─────────┘      └─────────────────┘ │
│                                        │                                    │
│ ┌──────────────────────┐               │                ┌─────────────────┐ │
│ │ Razorpay Webhooks    │ ──────────────┼──────────────> │ Upstash Redis   │ │
│ │ Live Payment Events  │               │                │ Managed Cache   │ │
│ └──────────────────────┘               ▼                └─────────────────┘ │
│                               ┌──────────────────┐                          │
│                               │ Groq Cloud API   │                          │
│                               │ Llama 3.3 70B    │                          │
│                               └──────────────────┘                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **🧠 AI & Inference** | Llama 3.3 70B Versatile via Groq Cloud API (~500 tok/s) |
| **⚡ Backend** | Python 3.12, FastAPI 0.115, SQLAlchemy 2.0, Pydantic v2, Uvicorn / Gunicorn |
| **🔐 Security** | JWT OAuth2 Authentication, RBAC (`admin`, `finance`, `auditor`), bcrypt password hashing, `slowapi` rate limiting (60 req/min) |
| **🎨 Frontend** | React 19, Vite 6, JavaScript ES6+, Vanilla CSS3 Design Tokens, Lucide Icons |
| **🗄️ Database & Cache** | PostgreSQL 16 (relational), Redis 7 (high-speed cache for cash flow & recon results), Alembic migrations |
| **🐳 DevOps & QA** | Docker Compose, Nginx TLS 1.3 reverse proxy, ngrok tunnel, Pytest, Locust load testing, Bandit security scanner |

---

## Platform

| Capability | What it covers |
|---|---|
| **Ingest production data** | Live Razorpay Webhooks (`payment.captured`, `settlement.processed`, `refund.processed`) with HMAC-SHA256 signature verification, and batch CSV/Excel drag-and-drop importer for Razorpay Settlement Reports & Tally/Zoho Books ledgers |
| **Scheduled Cron Trigger** | Production `/api/recon/cron` endpoint supporting both `GET` and `POST` methods, returning a lightweight JSON payload (~75 bytes) to prevent hosting platform log buffer overflows while running background reconciliation |
| **Schema Auto-Healing** | Built-in database schema inspector (`auto_heal_schema`) auto-migrates missing ORM table columns (`gateway`, `import_source`, `refund_amount`) on app startup without data loss |
| **4-Pass reconciliation** | Pass 1: Exact deterministic HashMap match. Pass 2: Rule-based T+1/T+2 date windows, MDR fee tolerance ±₹5, UTC/IST shifts, GST rounding. Pass 3: Fuzzy heuristics for partial refunds, 2% variance typos, duplicate ERP entries. Pass 4: LLM deep root-cause analysis |
| **AI diagnostics** | Bilingual English + Hinglish exception explanations with confidence scores, severity levels, recommended actions, and one-click Resolve/Escalate |
| **Cash flow projection** | 7-day forward liquidity based on pending captured orders with payment method MDR rates (UPI 0%, Card 2%, NetBanking 1.75%, Wallet 2.5%) |
| **What-If simulation** | Live "What-If" scenario engine updates cash flow curves instantaneously when breaks are resolved |
| **Real-time streaming** | Server-Sent Events (SSE) update the frontend pass-by-pass with animated progress counters |
| **Enterprise auth** | OAuth2/JWT, role-based access control, endpoint rate limiting |
| **Audit & export** | Complete audit trail per reconciliation run, JSON export, per-entry drill-down |


---

## 🚀 Step-by-Step Execution Guide

### Prerequisites

- [Python 3.12+](https://www.python.org/)
- [Node.js 20+](https://nodejs.org/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for containerized DB & Redis)
- A free Groq Cloud API Key from [console.groq.com](https://console.groq.com)

### Step 1: Clone & Infrastructure Setup

```bash
git clone https://github.com/Devesh-chandan/RazorRecon-AI-Autonomous-Settlement-Reconciliation-Cash-Flow-Prescriber.git
cd RazorRecon-AI-Autonomous-Settlement-Reconciliation-Cash-Flow-Prescriber

# Start PostgreSQL and Redis containers
docker compose up -d
```

### Step 2: Backend Setup & Database Migration

```bash
cd backend

# Create & activate virtual environment (Windows PowerShell)
python -m venv .venv
.venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Create environment file from template
copy ..\.env.example .env
```

Edit `backend/.env` and update your keys:

```env
GROQ_API_KEY=gsk_your_groq_api_key_here
RAZORPAY_WEBHOOK_SECRET=rzp_whsec_9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c
JWT_SECRET_KEY=242fdbce944b413db89346b5206bf59fdaef94ee0483ccb467662353050b9ddd
```

Run database migrations & seed initial data:

```bash
# Run database migrations (creates orders, settlements, erp_ledger, merchants, recon_runs tables)
alembic upgrade head

# Reset database back to clean 100 benchmark dataset (clears previous data)
python -m app.seed

# Start FastAPI dev server
uvicorn app.main:app --reload --port 8000
```

<details>
<summary><strong>Additional data management commands</strong></summary>

```bash
# Append N additional realistic records WITHOUT clearing existing DB data
python -m app.seed_append 50     # Appends 50 new records
python -m app.seed_append 500    # Appends 500 new records

# Clear ALL records from database completely (0 records state)
python -m app.reset

# Simulate live HMAC-SHA256 signed Razorpay webhooks over ngrok
python -m app.send_test_webhook
```

</details>

### Step 3: Frontend Setup

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Open **`http://localhost:5173`** in your browser.

### Step 4: Setup Live Razorpay Webhooks (Local Tunneling)

Since Razorpay servers need a public HTTPS endpoint to send webhook notifications to your local laptop:

<details>
<summary><strong>Using ngrok</strong></summary>

```bash
ngrok http 8000
```

Copy the forwarding URL (e.g. `https://pursuit-parcel-coat.ngrok-free.dev`).

</details>

<details>
<summary><strong>Using localtunnel (no signup required)</strong></summary>

```bash
npx localtunnel --port 8000
```

</details>

**Configure Razorpay Dashboard:**

1. Go to **Razorpay Dashboard ➔ Account & Settings ➔ Webhooks**.
2. Click **+ Add New Webhook**.
3. Set Webhook URL to: `https://<your-tunnel-subdomain>.ngrok-free.dev/api/webhooks/razorpay`
4. Enter Secret: `rzp_whsec_9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c` (matches `RAZORPAY_WEBHOOK_SECRET` in `.env`).
5. Select Active Events: `payment.captured`, `settlement.processed`, `refund.processed`.
6. Save. Live events will now be parsed, verified, and saved to PostgreSQL automatically.

**Quick Live Webhook Test (Simulator):**

```bash
python -m app.send_test_webhook
```

---

## 🔌 Port Mapping & Services

| Port | Service | URL | Purpose |
| :---: | :--- | :--- | :--- |
| `5173` | React 19 Frontend | [http://localhost:5173](http://localhost:5173) | Main Dashboard UI |
| `8000` | FastAPI Backend | [http://localhost:8000](http://localhost:8000) | REST API & SSE stream |
| `8000` | Swagger Docs | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive API documentation |
| `8000` | ReDoc | [http://localhost:8000/redoc](http://localhost:8000/redoc) | OpenAPI spec view |
| `443` | Nginx TLS Proxy | `https://localhost` | Production SSL reverse proxy |
| `5432` | PostgreSQL | `postgresql://localhost:5432` | Relational database |
| `6379` | Redis | `redis://localhost:6379` | Cash flow & recon results cache |

---

## 📥 Data Ingestion Pipelines

### 1. Live Webhook Listener (`POST /api/webhooks/razorpay`)

Verifies `X-Razorpay-Signature` using HMAC-SHA256 and automatically handles:

- `payment.captured` ➔ Inserts into `orders`
- `settlement.processed` ➔ Inserts into `settlements`
- `refund.processed` ➔ Updates order status to `refunded`

### 2. Batch CSV & Excel Importer (`POST /api/recon/upload`)

Ingests official Razorpay Settlement Reports (`.csv`, `.xlsx`) or ERP ledgers. Accepts `multipart/form-data` with `file` and `source` (`razorpay_settlement` or `erp_ledger`). Auto-maps headers, skips duplicate rows, and returns a JSON summary:

```json
{
  "source": "razorpay_settlement",
  "rows_read": 500,
  "rows_imported": 498,
  "rows_skipped": 2,
  "errors": []
}
```

Sample test datasets & JSON audit logs included in the production [`samples/`](samples/) directory:
- [`samples/sample_razorpay_settlements.csv`](samples/sample_razorpay_settlements.csv) — Sample Razorpay Settlement report
- [`samples/sample_erp_ledger.csv`](samples/sample_erp_ledger.csv) — Sample ERP Sales Ledger file
- [`samples/sample_audit_log_export.json`](samples/sample_audit_log_export.json) — Sample JSON audit log export


### 3. Production Cron Reconciliation Trigger (`GET` / `POST /api/recon/cron`)

Designed for cloud cron job providers (e.g. `cron-job.org`, Render Cron, GitHub Actions, AWS EventBridge). Accepts both `GET` and `POST` methods and returns a lightweight HTTP 200 JSON status response (~75 bytes) to prevent response buffer overflows while executing reconciliation asynchronously in the background:

```json
{
  "status": "ok",
  "message": "Reconciliation job started",
  "run_id": "c71a39f6-1234-4567-89ab-cdef01234567"
}
```

Included runner script: [`scripts/cron_recon.sh`](scripts/cron_recon.sh).

---

## 🔐 Authentication Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Creates a new merchant account with hashed password (`bcrypt`) |
| `POST` | `/api/auth/token` | OAuth2 login endpoint. Returns JWT token valid for 8 hours |
| `GET` | `/api/auth/me` | Returns current authenticated merchant profile (requires `Bearer <token>`) |

---

## 🔌 Complete API Reference

Interactive Swagger documentation is available at **`http://localhost:8000/docs`** when the backend is running.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/webhooks/razorpay` | Live Webhook Listener — HMAC-SHA256 signature verification |
| `POST` | `/api/recon/upload` | Batch Importer — `.csv` / `.xlsx` ingestion |
| `GET` / `POST` | `/api/recon/cron` | Lightweight Cron Trigger — HTTP 200 response (~75 bytes) |
| `POST` | `/api/auth/register` | Register new merchant user |
| `POST` | `/api/auth/token` | OAuth2 password login, returns JWT |
| `GET` | `/api/auth/me` | Current authenticated user profile |
| `POST` | `/api/recon/run?scope=all` | Trigger 4-pass reconciliation (`scope=all` or `scope=imported`) |
| `GET` | `/api/recon/stream/{run_id}` | SSE Stream — real-time pass completion events |
| `GET` | `/api/recon/results/{run_id}` | Detailed results for all records from Redis/DB |
| `GET` | `/api/recon/stats/{run_id}` | Aggregated KPIs (match rate %, net payout, break count) |
| `GET` | `/api/cashflow/{run_id}` | 7-day forward cash-flow projection curve |
| `POST` | `/api/cashflow/whatif` | Simulate resolving a break, returns updated cash curve |
| `GET` | `/api/audit/{run_id}` | Complete audit log for a specific run |
| `GET` | `/api/audit/{run_id}/export` | Download full audit log as JSON |
| `GET` | `/api/health` | Health check — DB, Redis, and Groq API status |


---

## 🗄️ Database & Cache Inspection

<details>
<summary><strong>🐘 PostgreSQL (Port 5432)</strong></summary>

**Connection:** Host `localhost` · Port `5432` · Database `razorrecon` · User `razorrecon` · Password `razorrecon`

**CLI via Docker:**
```bash
docker exec -it razorrecon_postgres psql -U razorrecon -d razorrecon
```

**Useful queries:**
```sql
SELECT count(*) FROM orders;
SELECT count(*) FROM settlements;
SELECT run_id, status, match_rate, created_at FROM recon_runs ORDER BY created_at DESC LIMIT 5;
```

**GUI Tools:** Connect via TablePlus, DBeaver, pgAdmin, or VS Code Database Client with the credentials above.

</details>

<details>
<summary><strong>🔴 Redis (Port 6379)</strong></summary>

**Connection:** Host `localhost` · Port `6379` · URL `redis://localhost:6379/0`

**CLI via Docker:**
```bash
docker exec -it razorrecon_redis redis-cli
```

**Useful commands:**
```redis
PING                           # Returns PONG
KEYS razorrecon:*              # Inspect all cached reconciliation runs
GET razorrecon:results:<run_id> # Retrieve cached JSON result for a run
```

**GUI Tools:** Use [RedisInsight](https://redis.io/insight/) ➔ Add Database ➔ Host: `localhost`, Port: `6379`.

</details>

---

## 🐳 Production Deployment

For multi-worker high-availability deployment with Docker Compose + Gunicorn + Nginx:

<details>
<summary><strong>Deployment steps</strong></summary>

**1. Generate self-signed SSL certificate (or use Let's Encrypt):**

```powershell
New-Item -ItemType Directory -Force -Path ".\nginx\ssl"
openssl req -x509 -newkey rsa:4096 -sha256 -days 365 -nodes `
  -keyout .\nginx\ssl\selfsigned.key -out .\nginx\ssl\selfsigned.crt `
  -subj "/CN=localhost/O=RazorRecon/C=IN"
```

**2. Build and launch production stack:**

```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

This launches:
- **`backend`**: Gunicorn running 4 Uvicorn worker processes
- **`nginx`**: HTTPS reverse proxy on port 443 with TLS 1.2/1.3, security headers, gzip, and 60MB upload limit
- **`postgres`**: Internal PostgreSQL container with health checks
- **`redis`**: Internal Redis 7 container with password auth

</details>

---

## 🧪 Testing & Quality Assurance

```bash
# Run unit & integration tests
pytest tests/ -v

# Run security vulnerability audit
bandit -r backend/

# Run load & concurrency benchmark (100-500 concurrent users)
locust -f tests/locustfile.py --headless -u 100 -r 10 --run-time 60s --host http://localhost:8000
```

---

## 📁 Repository Structure

```
RazorRecon-AI/
├── .github/
│   └── workflows/
│       └── ci.yml            # GitHub Actions automated test & build pipeline
├── backend/
│   ├── alembic/              # Database migration scripts
│   │   └── versions/         # Migration revisions (0001_initial, 0002_add_merchants, 0003_add_gateway_fields)
│   ├── app/
│   │   ├── auth/             # JWT auth, bcrypt password hashing, RBAC dependencies
│   │   ├── engine/           # 4-Pass Reconciliation Core (pass1-4, cashflow, reconcile)
│   │   ├── llm/              # Groq client & diagnostic prompts
│   │   ├── routes/           # FastAPI routers (recon, cashflow, audit, auth, ingestion, health)
│   │   ├── config.py         # Settings & environment variables
│   │   ├── database.py       # SQLAlchemy database session manager & auto_heal_schema inspector
│   │   ├── models.py         # DB ORM Schema definitions
│   │   ├── schemas.py        # Pydantic request/response schemas
│   │   ├── cache.py          # Redis caching implementation
│   │   ├── seed.py           # Benchmark dataset seeder (100 records, 10 edge cases)
│   │   └── main.py           # FastAPI Entrypoint + slowapi rate limiting + CORS preflight
│   ├── alembic.ini
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/              # API REST & SSE client
│   │   ├── components/       # Workbench, CashFlowChart, AIExceptionDrawer, AuditLog, Modal
│   │   ├── App.jsx
│   │   └── index.css         # Razorpay Design System tokens & styles
│   └── package.json
├── samples/                  # Production sample datasets & JSON audit log exports
│   ├── sample_razorpay_settlements.csv
│   ├── sample_erp_ledger.csv
│   └── sample_audit_log_export.json
├── scripts/
│   └── cron_recon.sh         # Production cron job trigger shell script
├── tests/                    # Pytest & Locust test suite
│   ├── conftest.py           # Path resolver for IDEs & test runners
│   ├── test_cron_logging.py  # Unit tests for cron endpoint & logging configuration
│   ├── test_pass1_exact.py   # Unit tests for Pass 1 Exact Match logic
│   ├── test_reconcile.py     # Unit tests for Pass 2-3 & multi-pass engine pipeline
│   ├── test_webhook.py       # Unit tests for HMAC-SHA256 webhook verification
│   ├── test_csv_importer.py  # Unit tests for CSV/Excel batch importer (with autouse cleanup)
│   └── locustfile.py        # Concurrency & load benchmark suite
├── nginx/                    # Nginx TLS proxy configuration & SSL cert instructions
├── docs/images/              # README screenshots & architecture diagrams
├── Dockerfile                # Multi-stage Gunicorn ASGI production container
├── docker-compose.yml        # Development PostgreSQL 16 & Redis 7
├── docker-compose.prod.yml   # Production stack (backend + nginx + postgres + redis)
├── Makefile                  # Developer & judge command shortcuts (make dev, make test)
├── quickstart.sh             # 1-click automated setup script for judges
├── LICENSE                   # MIT License
├── PROBLEMS_AND_SOLUTIONS.md # Complete problem, root-cause & solution log
├── pytest.ini
├── .env.example
└── README.md
```

---

## 📘 Troubleshooting & Problem Log

For a complete record of all technical issues faced during integration, webhook troubleshooting, and their exact solutions, see **[`PROBLEMS_AND_SOLUTIONS.md`](PROBLEMS_AND_SOLUTIONS.md)**.

---

## 🏆 Hackathon Submission

| Field | Value |
|---|---|
| **Live Demo** | [https://razor-recon-ai-autonomous-settlemen.vercel.app/](https://razor-recon-ai-autonomous-settlemen.vercel.app/) |
| **Track** | Razorpay Buildathon 2026 — Track 04 (AI Finance Controller) |
| **Model** | Llama 3.3 70B Versatile (via Groq Cloud API) |
| **License** | MIT |
| **Author** | Devesh Chandan |

---

<p align="center">
  <i>Built with ❤️ for Razorpay Buildathon 2026</i>
</p>