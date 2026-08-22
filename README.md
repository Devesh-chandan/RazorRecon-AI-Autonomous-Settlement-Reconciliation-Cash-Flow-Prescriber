# RazorRecon & Flow ⚡

**LLM-Powered Autonomous Settlement Reconciliation & Cash-Flow Prescriber**  
*Built for Razorpay Buildathon 2026 · Track 04: AI Finance Controller*

---

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19.0-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![Vite 6](https://img.shields.io/badge/Vite-6.0-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis 7](https://img.shields.io/badge/Redis-7.0-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Llama 3.3 70B](https://img.shields.io/badge/LLM-Llama_3.3_70B-0467DF?style=for-the-badge&logo=meta&logoColor=white)](https://groq.com/)
[![Groq Cloud API](https://img.shields.io/badge/Inference-Groq_Cloud-F05032?style=for-the-badge&logo=speedtest&logoColor=white)](https://groq.com/)

---

## 📌 Executive Summary & Problem Recap

Razorpay merchants receive daily **net settlements** that lump captured orders, Merchant Discount Rate (MDR) gateway fees, 18% GST on MDR, refunds, and chargebacks into single bulk bank credits. Matching these net payout rows against internal ERP order books across T+1/T+2 settlement cycles is:
- ⏳ **Time-Intensive**: Mid-sized merchants spend 20–40 hours per week manually auditing spreadsheets.
- ⚠️ **Error-Prone**: Human error leads to unrecorded breaks, missed tax deductions, and duplicate ledger entries.
- 🌫️ **Cash Opaque**: Unresolved breaks obscure usable operating capital and forward liquidity.

**RazorRecon & Flow** addresses this with an autonomous enterprise architecture:
1. **Real-World Production Data Ingestion**: Ingests live Razorpay Webhooks (`payment.captured`, `settlement.processed`, `refund.processed`) with HMAC-SHA256 signature verification AND batch CSV/Excel importer for Razorpay Settlement Reports & Tally / Zoho Books sales ledgers.
2. **Multi-Pass Reconciliation Pipeline**: Achieves **>90% automated match rate** across complex synthetic & live settlement batches containing real-world edge cases.
3. **Bilingual AI Exception Diagnostics**: Uses **Llama 3.3 70B via Groq** (~500 tok/s) to diagnose root causes and prescribe resolution steps in plain **English & Hinglish**.
4. **Enterprise Auth & Rate Limiting**: OAuth2 / JWT Authentication with Role-Based Access Control (RBAC) and `slowapi` rate limiting.
5. **7-Day Forward Cash-Flow Prescriber**: Computes expected daily settlement inflows and updates forward liquidity in real-time as settlement breaks are resolved via "What-If" simulation.

---

## 🔌 Port Mapping & Documentation Services

Below is the complete table of all ports and services configured across the project:

| Port | Service / Component | Protocol / Type | URL / Endpoint | Purpose |
| :---: | :--- | :---: | :--- | :--- |
| **`5173`** | **React 19 Frontend** | HTTP | [http://localhost:5173](http://localhost:5173) | Main Razorpay Recon & Flow Dashboard UI |
| **`8000`** | **FastAPI Backend Server** | HTTP / SSE | [http://localhost:8000](http://localhost:8000) | REST API & Server-Sent Events progress stream |
| **`8000`** | **Swagger OpenAPI Docs** | HTTP / UI | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive API documentation & live testing console |
| **`8000`** | **ReDoc API Docs** | HTTP / UI | [http://localhost:8000/redoc](http://localhost:8000/redoc) | OpenAPI spec documentation view |
| **`443`** | **Production Nginx TLS Proxy** | HTTPS | `https://localhost` | SSL reverse proxy for FastAPI & Static Frontend |
| **`5432`** | **PostgreSQL Database** | TCP / SQL | `postgresql://localhost:5432` | Relational storage for orders, settlements, merchants & recon runs |
| **`6379`** | **Redis Cache Server** | TCP / In-Memory | `redis://localhost:6379` | Fast caching layer for 7-day cash flow projections |

---

## 🔥 Key Features

- **📡 Real-World Production Data Ingestion**:
  - **Live Razorpay Webhook Handler** (`POST /api/webhooks/razorpay`): Validates `X-Razorpay-Signature` header using HMAC-SHA256 merchant secret. Parses `payment.captured`, `settlement.processed`, and `refund.processed` JSON payloads into PostgreSQL in real-time.
  - **Batch CSV & Excel Importer** (`POST /api/recon/upload`): Auto-maps column headers (`Order ID`, `UTR`, `MDR Fee`, `GST`, `Net Credit`, `Recorded Amount`) from Razorpay Settlement Reports & Tally / Zoho Books sales ledgers with duplicate row skipping and detailed per-row error reporting.
- **🔐 Enterprise Security & JWT Authentication**:
  - OAuth2 / JWT Authentication (`POST /api/auth/register`, `POST /api/auth/token`, `GET /api/auth/me`) with `bcrypt` password hashing via `passlib`.
  - Role-Based Access Control (RBAC) supporting `admin`, `finance`, and `auditor` user roles.
  - Endpoint Rate Limiting (`slowapi`) preventing API flooding & brute force attacks (60 req/min per IP).
- **⚡ 4-Pass Hybrid Reconciliation Engine**:
  - **Pass 1 (Exact Deterministic)**: Instant HashMap lookup matching `order_id` + `amount`.
  - **Pass 2 (Rule-Based Contextual)**: Handles T+1/T+2 date windows, MDR fee tolerances (±₹5), cross-midnight UTC/IST boundary shifts, and GST rounding differences.
  - **Pass 3 (Fuzzy Heuristics)**: Detects net partial refund adjustments, data entry typos within 2% variance, chargeback holdbacks, and duplicate ERP entries.
  - **Pass 4 (LLM Diagnostics)**: Sends remaining complex breaks to Llama 3.3 70B for deep root-cause analysis and actionable fix recommendations.
- **🌐 Bilingual AI Exception Drawer (English + Hinglish)**:
  - Generates clear, non-technical explanations in both English and natural Hinglish (e.g., *"Yeh payment T+2 settlement cycle ki wajeh se delay hua hai..."*).
- **📈 Forward Cash-Flow Prescriber & "What-If" Simulator**:
  - Projects 7-day forward liquidity based on pending captured orders and payment method MDR rates (UPI 0%, Card 2%, NetBanking 1.75%, Wallet 2.5%).
  - Live "What-If" scenario engine updates cash curves instantaneously when breaks are resolved.
- **📡 Real-Time SSE Streaming**:
  - Live Server-Sent Events (SSE) update the frontend UI pass-by-pass with animated progress counters.

---

## 🏗️ Architecture Overview

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

## 🚀 Step-by-Step Execution Guide

### Prerequisites
- [Python 3.12+](https://www.python.org/)
- [Node.js 20+](https://nodejs.org/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for containerized DB & Redis)
- A free Groq Cloud API Key from [console.groq.com](https://console.groq.com)

---

### Step 1: Clone & Infrastructure Setup

```bash
git clone https://github.com/Devesh-chandan/RazorRecon-AI-Autonomous-Settlement-Reconciliation-Cash-Flow-Prescriber.git
cd RazorRecon-AI-Autonomous-Settlement-Reconciliation-Cash-Flow-Prescriber

# Start PostgreSQL and Redis containers
docker compose up -d
```

---

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

# Seed 100 synthetic benchmark records
python -m app.seed

# Start FastAPI dev server
uvicorn app.main:app --reload --port 8000
```

---

### Step 3: Frontend Setup

In a new terminal:
```bash
cd frontend
npm install
npm run dev
```

Open **`http://localhost:5173`** in your browser.

---

### Step 4: Setup Live Razorpay Webhooks (Local Tunneling)

Since Razorpay servers need a public HTTPS endpoint to send webhook notifications to your local laptop:

#### Using `ngrok`:
```bash
cd C:\Users\HP\Downloads\ngrok-v3-stable-windows-amd64
.\ngrok.exe http 8000
```
*Copy the forwarding URL (e.g. `https://pursuit-parcel-coat.ngrok-free.dev`).*

#### Alternative (using `localtunnel` — no signup required):
```bash
npx localtunnel --port 8000
```

#### Configure Razorpay Dashboard:
1. Go to **Razorpay Dashboard ➔ Account & Settings ➔ Webhooks**.
2. Click **+ Add New Webhook**.
3. Set Webhook URL to: `https://<your-tunnel-subdomain>.ngrok-free.dev/api/webhooks/razorpay`
4. Enter Secret: `rzp_whsec_9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c` (matches `RAZORPAY_WEBHOOK_SECRET` in `.env`).
5. Select Active Events:
   - `payment.captured`
   - `settlement.processed`
   - `refund.processed`
6. Save. Live events will now be parsed, verified, and saved to PostgreSQL automatically!

---

## 📥 Production Data Ingestion Pipelines

### 1. Live Webhook Listener (`POST /api/webhooks/razorpay`)
- Verifies `X-Razorpay-Signature` using HMAC-SHA256.
- Automatically handles:
  - `payment.captured` ➔ Inserts into `orders`.
  - `settlement.processed` ➔ Inserts into `settlements`.
  - `refund.processed` ➔ Updates order status to `refunded`.

### 2. Batch CSV & Excel Importer (`POST /api/recon/upload`)
- Ingests official Razorpay Settlement Reports (`.csv`, `.xlsx`) or ERP ledgers.
- Accepts `multipart/form-data` with `file` and `source` (`razorpay_settlement` or `erp_ledger`).
- Auto-maps headers, skips duplicate rows, and returns JSON summary:
  ```json
  {
    "source": "razorpay_settlement",
    "rows_read": 500,
    "rows_imported": 498,
    "rows_skipped": 2,
    "errors": []
  }
  ```

---

## 🔐 Enterprise Authentication Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Creates a new merchant account with hashed password (`bcrypt`). |
| `POST` | `/api/auth/token` | OAuth2 login endpoint. Returns JWT token valid for 8 hours. |
| `GET` | `/api/auth/me` | Returns current authenticated merchant profile (requires `Bearer <token>`). |

---

## 🐳 Production Deployment (Docker Compose + Gunicorn + Nginx)

For multi-worker high-availability deployment:

1. Generate self-signed SSL certificate (or use Let's Encrypt):
   ```powershell
   New-Item -ItemType Directory -Force -Path ".\nginx\ssl"
   openssl req -x509 -newkey rsa:4096 -sha256 -days 365 -nodes -keyout .\nginx\ssl\selfsigned.key -out .\nginx\ssl\selfsigned.crt -subj "/CN=localhost/O=RazorRecon/C=IN"
   ```

2. Build and launch production stack:
   ```bash
   docker-compose -f docker-compose.prod.yml up --build -d
   ```

This launches:
- **`backend`**: Gunicorn running 4 Uvicorn worker processes (`gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app`).
- **`nginx`**: HTTPS reverse proxy on port 443 with TLS 1.2/1.3, security headers, gzip, and 60MB upload limit.
- **`postgres`**: Internal PostgreSQL container with health checks.
- **`redis`**: Internal Redis 7 container with password auth.

---

## 🧪 Testing & Quality Assurance

### Run Unit & Integration Tests
```bash
# Run pytest across webhook signature verification and CSV importer logic
pytest tests/ -v
```

### Run Security Vulnerability Audit
```bash
# Run bandit security scanner across backend
bandit -r backend/
```

### Run Load & Concurrency Benchmark
```bash
# Run Locust load test (simulates 100-500 concurrent users)
locust -f tests/locustfile.py --headless -u 100 -r 10 --run-time 60s --host http://localhost:8000
```

---

## 🔌 Complete API Endpoint Reference

Interactive Swagger documentation is available at **`http://localhost:8000/docs`** when the backend is running.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/webhooks/razorpay` | **Live Webhook Listener** — Ingests Razorpay payment, settlement & refund events with HMAC-SHA256 signature check. |
| `POST` | `/api/recon/upload` | **Batch Importer** — Ingests `.csv` or `.xlsx` Razorpay settlement reports or ERP ledgers. |
| `POST` | `/api/auth/register` | Registers new merchant user account. |
| `POST` | `/api/auth/token` | OAuth2 password login, returns JWT token. |
| `GET` | `/api/auth/me` | Gets current authenticated user profile. |
| `POST` | `/api/recon/run` | Triggers a new 4-pass reconciliation run. Returns `run_id`. |
| `GET` | `/api/recon/stream/{run_id}` | **SSE Stream** — Streams real-time pass completion events. |
| `GET` | `/api/recon/results/{run_id}` | Retrieves detailed results for all records from Redis/DB. |
| `GET` | `/api/recon/stats/{run_id}` | Returns aggregated KPIs (Match rate %, net payout, break count). |
| `GET` | `/api/cashflow/{run_id}` | Returns 7-day forward cash-flow projection curve. |
| `POST` | `/api/cashflow/whatif` | Simulates resolving a break and returns updated cash curve. |
| `GET` | `/api/audit/{run_id}` | Retrieves complete audit log history for a specific run. |
| `GET` | `/api/audit/{run_id}/export` | Downloads the full audit log as a JSON file. |
| `GET` | `/api/health` | Health check endpoint monitoring DB, Redis, and Groq API status. |

---

## 📁 Repository Structure

```
RazorRecon-AI/
├── backend/
│   ├── alembic/              # Database migration scripts
│   │   └── versions/         # Migration revisions (0001_initial, 0002_add_merchants)
│   ├── app/
│   │   ├── auth/             # JWT auth, bcrypt password hashing, RBAC dependencies
│   │   │   ├── jwt.py
│   │   │   ├── dependencies.py
│   │   │   └── models.py
│   │   ├── engine/           # 4-Pass Reconciliation Core
│   │   │   ├── pass1_exact.py
│   │   │   ├── pass2_rules.py
│   │   │   ├── pass3_fuzzy.py
│   │   │   ├── pass4_llm.py
│   │   │   ├── cashflow.py
│   │   │   └── reconcile.py
│   │   ├── llm/              # Groq client & diagnostic prompts
│   │   ├── routes/           # FastAPI routers (recon, cashflow, audit, auth, ingestion, health)
│   │   │   ├── auth.py
│   │   │   ├── ingestion.py
│   │   │   ├── recon.py
│   │   │   ├── cashflow.py
│   │   │   ├── audit.py
│   │   │   └── health.py
│   │   ├── config.py         # Settings & environment variables
│   │   ├── database.py       # SQLAlchemy database session manager
│   │   ├── models.py         # DB ORM Schema definitions
│   │   ├── schemas.py        # Pydantic request/response schemas
│   │   ├── cache.py          # Redis caching implementation
│   │   ├── seed.py           # Synthetic dataset seeder
│   │   └── main.py           # FastAPI Entrypoint + slowapi rate limiting
│   ├── alembic.ini
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/              # API REST & SSE client
│   │   ├── components/       # Header, KPIRow, ReconWorkbench, CashFlowChart, AIExceptionDrawer, AuditLogPanel, Sidebar
      │   │   ├── context/          # Reconciliation State Context
│   │   ├── App.jsx
│   │   └── index.css         # Razorpay Design System tokens & styles
│   └── package.json
├── nginx/                    # Nginx TLS proxy configuration & SSL cert instructions
│   ├── nginx.conf
│   └── README.md
├── tests/                    # Pytest & Locust test suite
│   ├── test_webhook.py
│   ├── test_csv_importer.py
│   └── locustfile.py
├── Dockerfile                # Multi-stage Gunicorn ASGI production container
├── docker-compose.yml        # Development PostgreSQL 16 & Redis 7
├── docker-compose.prod.yml   # Production stack (backend + nginx + postgres + redis)
├── pytest.ini
├── .env.example
└── README.md
```

---

## 🏆 Hackathon Submission Metadata

- **Track**: Razorpay Buildathon 2026 — Track 04 (AI Finance Controller)
- **Model**: Llama 3.3 70B Versatile (via Groq Cloud API)
- **License**: MIT
- **Author**: Devesh Chandan

---

<p align="center">
  <i>Built with ❤️ for Razorpay Buildathon 2026</i>
</p>