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

**RazorRecon & Flow** addresses this with an autonomous dual-engine architecture:
1. **Multi-Pass Reconciliation Pipeline**: Achieves **>90% automated match rate** across complex 100-record synthetic settlement batches containing real-world edge cases.
2. **Bilingual AI Exception Diagnostics**: Uses **Llama 3.3 70B via Groq** (~500 tok/s) to diagnose root causes and prescribe resolution steps in plain **English & Hinglish**.
3. **7-Day Forward Cash-Flow Prescriber**: Computes expected daily settlement inflows and updates forward liquidity in real-time as settlement breaks are resolved via "What-If" simulation.

---

## 🔌 Port Mapping & Documentation Services

Below is the complete table of all ports and services configured across the project:

| Port | Service / Component | Protocol / Type | URL / Endpoint | Purpose |
| :---: | :--- | :---: | :--- | :--- |
| **`5173`** | **React 19 Frontend** | HTTP | [http://localhost:5173](http://localhost:5173) | Main Razorpay Recon & Flow Dashboard UI |
| **`8000`** | **FastAPI Backend Server** | HTTP / SSE | [http://localhost:8000](http://localhost:8000) | REST API & Server-Sent Events progress stream |
| **`8000`** | **Swagger OpenAPI Docs** | HTTP / UI | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive API documentation & live testing console |
| **`8000`** | **ReDoc API Docs** | HTTP / UI | [http://localhost:8000/redoc](http://localhost:8000/redoc) | OpenAPI spec documentation view |
| **`5432`** | **PostgreSQL Database** | TCP / SQL | `postgresql://localhost:5432` | Relational storage for orders, settlements & recon runs |
| **`6379`** | **Redis Cache Server** | TCP / In-Memory | `redis://localhost:6379` | Fast caching layer for 7-day cash flow projections |
| **`3000`** | **Alternative Frontend Port** | HTTP | `http://localhost:3000` | Configured fallback CORS origin for React/Next dev |

---

## 🔥 Key Features

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
- **🎨 Razorpay Dashboard Fidelity**:
  - Built with Razorpay's light design language (Mulish typography, brand color `#2D81E0`, crisp KPI cards, status badges, and interactive Recharts graphs).

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        BROWSER (React 19 + Vite)                     │
│                                                                      │
│  ┌──────────┐ ┌─────────────┐ ┌──────────────┐ ┌────────────────┐   │
│  │  Header   │ │  KPI Cards  │ │ Recon Table  │ │ Cash-Flow Chart│   │
│  └──────────┘ └─────────────┘ └──────┬───────┘ └───────┬────────┘   │
│                                      │                  │            │
│  ┌───────────────────────────────────┐│ ┌───────────────┐            │
│  │     AI Exception Drawer          ││ │  Audit Log    │            │
│  └───────────────────────────────────┘│ └───────────────┘            │
│                                       │                              │
└───────────────────────────────────────┼──────────────────────────────┘
                                        │ REST API + SSE Stream
                                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    BACKEND (Python 3.12 + FastAPI)                    │
│                                                                      │
│  ┌─────────────┐  ┌──────────────────┐  ┌────────────────────────┐  │
│  │ API Routes  │  │  Recon Engine    │  │   LLM Service          │  │
│  │ /api/recon  │──│  4-Pass Pipeline │──│   Groq + Llama 3.3     │  │
│  │ /api/cash   │  │  Deterministic   │  │   Exception Diagnostics│  │
│  │ /api/audit  │  │  + LLM Hybrid    │  │   Bilingual Narratives │  │
│  └──────┬──────┘  └────────┬─────────┘  └────────────────────────┘  │
│         │                  │                                         │
│         ▼                  ▼                                         │
│  ┌─────────────┐  ┌──────────────┐                                  │
│  │  Redis 7    │  │ PostgreSQL 16│                                  │
│  │  Cache +    │  │  Orders      │                                  │
│  │  SSE State  │  │  Settlements │                                  │
│  │             │  │  Recon Runs  │                                  │
│  └─────────────┘  └──────────────┘                                  │
│                                                                      │
│         Docker Compose (postgres:16 + redis:7)                       │
└──────────────────────────────────────────────────────────────────────┘
```

### Production Alignment Matrix

| Razorpay Architecture | RazorRecon Equivalent | Alignment |
|---|---|---|
| Microservices on AWS EKS | Python 3.12 FastAPI Service | Containerized microservice pattern |
| PostgreSQL / MySQL | PostgreSQL 16 | Direct match with Razorpay production DBs |
| Redis Cache | Redis 7 (with DB fallback) | Cache layer for high-throughput recon runs |
| Event-Driven Kafka Stream | Server-Sent Events (SSE) | Real-time live status updates to browser |
| LLM / Agent Orchestration | Llama 3.3 70B via Groq Cloud API | Ultra-fast (~500 tok/s) open LLM inference |
| Airflow Batch DAGs | Automated 4-Pass Pipeline | Simulated scheduled reconciliation DAG |

---

## ⚙️ Reconciliation Pipeline (4-Pass Engine)

```
┌─────────────────────────────────────────────────────┐
│                  INPUT (PostgreSQL)                 │
│   orders + settlements + erp_ledger tables           │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  PASS 1: EXACT │   Match on order_id + payment_id
              │  DETERMINISTIC │   + exact ₹ amount (50 clean matches)
              └───────┬────────┘
                      │ SSE progress update
                      ▼
              ┌────────────────┐
              │  PASS 2: RULE  │   T+1/T+2 window, MDR tolerance (±₹5),
              │  BASED         │   cross-midnight IST, GST rounding
              └───────┬────────┘
                      │ SSE progress update
                      ▼
              ┌────────────────┐
              │  PASS 3: FUZZY │   Amount proximity (±2%), partial refund
              │  HEURISTIC     │   net-matching, duplicate ERP detection
              └───────┬────────┘
                      │ SSE progress update
                      ▼
              ┌────────────────┐
              │  PASS 4: LLM   │   Llama 3.3 70B analyzes remaining
              │  DIAGNOSTICS   │   unmatched breaks with full context
              └───────┬────────┘
                      │ Final results cached in Redis & persisted to PostgreSQL
                      ▼
              ┌────────────────┐
              │ Output Summary │   93% Match Rate | 7 Unresolved Breaks
              └────────────────┘
```

---

## 🧪 Synthetic Dataset Edge Cases (No Cherry-Picking)

The benchmark dataset contains **100 records** seeded with real-world payment processing anomalies:

| # | Edge Case | Seeded Behavior | Record Count |
|---|---|---|---|
| 1 | **MDR Rate Variance** | Gateway fee deviates ±₹0.50–₹5.00 from expected percentage | 8 |
| 2 | **T+2 Timing Lag** | Settlement date delayed by 2 days; appears missing on T+1 audit | 10 |
| 3 | **Cross-Midnight Boundary** | Created at 23:45 IST, captured at 00:02 IST next calendar day | 5 |
| 4 | **Full Refunds** | Refund settlement with matching debit amount | 6 |
| 5 | **Partial Refunds** | Net credit reflects partial refund deduction | 4 |
| 6 | **Chargeback Holdbacks** | Adjustment entity with negative net credit; no ERP entry | 3 |
| 7 | **Missing ERP Entry** | Gateway settlement exists but unrecorded in merchant ERP | 4 |
| 8 | **Duplicate ERP Entry** | Same `order_id` recorded twice in ERP with different amounts | 2 |
| 9 | **Amount Entry Typo** | ERP recorded amount differs by ≤2% from gateway credit | 5 |
| 10 | **GST Rounding** | Tax calculation differs by ₹0.01 vs standard 18% MDR tax rate | 3 |
| — | **Clean Exact Matches** | Perfect 1-to-1 match across Order, Settlement, and ERP | 50 |

---

## 🧰 Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, `sse-starlette`
- **Database & Caching**: PostgreSQL 16, Redis 7 (Docker Compose)
- **AI / LLM**: Groq Cloud API (`groq` SDK) running `llama-3.3-70b-versatile`
- **Frontend**: React 19, Vite 6, Recharts, Lucide React icons, Native EventSource API
- **Styling**: Vanilla CSS with custom design tokens, Mulish typography, JetBrains Mono

---

## 🚀 Quick Start Guide

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed & running
- [Python 3.12+](https://www.python.org/)
- [Node.js 20+](https://nodejs.org/)
- A free Groq Cloud API Key from [consolegroq.com](https://console.groq.com)

---

### 1. Clone & Infrastructure Setup

```bash
git clone https://github.com/Devesh-chandan/RazorRecon-AI-Autonomous-Settlement-Reconciliation-Cash-Flow-Prescriber.git
cd RazorRecon-AI-Autonomous-Settlement-Reconciliation-Cash-Flow-Prescriber

# Start PostgreSQL and Redis containers
docker compose up -d
```

---

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create & activate virtual environment (Windows PowerShell / CMD)
python -m venv .venv
.venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Create environment configuration file
copy ..\.env.example .env

# ⚠️ Edit .env and set your GROQ_API_KEY
# GROQ_API_KEY=gsk_your_actual_key_here

# Run database migrations
alembic upgrade head

# Seed 100 synthetic records with built-in edge cases
python -m app.seed

# Launch the FastAPI dev server
uvicorn app.main:app --reload --port 8000
```

---

### 3. Frontend Setup

In a new terminal:

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```

Open your browser and navigate to **`http://localhost:5173`**.

---

## 🔑 Environment Variables

### Backend Configuration (`backend/.env`)

```ini
# Groq Cloud API Key for Llama 3.3 70B inference
GROQ_API_KEY=gsk_your_groq_api_key_here

# PostgreSQL Database Connection URL
DATABASE_URL=postgresql://razorrecon:razorrecon@localhost:5432/razorrecon

# Redis Cache Connection URL
REDIS_URL=redis://localhost:6379/0
```

### Frontend Configuration (`frontend/.env`)

```ini
# Backend API Base URL
VITE_API_URL=http://localhost:8000
```

---

## 🔌 API Reference & Endpoints

Interactive Swagger documentation is available at **`http://localhost:8000/docs`** when the backend is running.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/recon/run` | Triggers a new 4-pass reconciliation run. Returns `run_id`. |
| `GET` | `/api/recon/stream/{run_id}` | **SSE Stream** — Streams real-time pass completion events. |
| `GET` | `/api/recon/results/{run_id}` | Retrieves detailed results for all 100 records from Redis/DB. |
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
│   ├── app/
│   │   ├── engine/           # 4-Pass Reconciliation Core
│   │   │   ├── pass1_exact.py
│   │   │   ├── pass2_rules.py
│   │   │   ├── pass3_fuzzy.py
│   │   │   ├── pass4_llm.py
│   │   │   ├── cashflow.py
│   │   │   └── reconcile.py
│   │   ├── llm/              # Groq client & diagnostic prompts
│   │   ├── routes/           # FastAPI REST & SSE routers
│   │   ├── config.py         # Settings & environment variables
│   │   ├── database.py       # SQLAlchemy database session manager
│   │   ├── models.py         # DB ORM Schema definitions
│   │   ├── schemas.py        # Pydantic request/response schemas
│   │   ├── cache.py          # Redis caching implementation
│   │   ├── seed.py           # Synthetic dataset seeder (100 records)
│   │   └── main.py           # FastAPI Application Entrypoint
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
├── docker-compose.yml        # PostgreSQL 16 & Redis 7 Docker services
├── .env.example
├── implementation_plan.md    # Detailed architectural design document
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