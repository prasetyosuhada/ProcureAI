# ProcureAI 🤖💼
**Enterprise-Grade Agentic Procurement Automation**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_Workflow-FF5722.svg)]()
[![React](https://img.shields.io/badge/React-18-61DAFB.svg?logo=react)]()
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg?logo=postgresql)]()

ProcureAI is an agentic AI platform that automates the end-to-end procurement lifecycle — from Purchase Requisition (PR) through Purchase Order (PO), Goods Receipt (GR), and Invoice matching. 

By leveraging a **Supervisor/Orchestrator pattern**, the system coordinates specialized AI agents with **Human-in-the-Loop (HITL)** approval gates, enabling high-precision automation while maintaining rigorous financial governance.

---

## 🌟 Why Agentic Workflow?

Traditional procurement systems rely on rigid rule-engines for 3-way invoice matching (PO vs. GR vs. Invoice). These engines fail when faced with unstructured vendor invoices, partial deliveries with combined billing, or subtle price-variance edge cases. 

ProcureAI solves this by using a **LangGraph-driven Agentic Workflow** where the **Invoice Matching Agent** acts as an intelligent AP Clerk. It doesn't just flag a mismatch—it generates an **explainable reasoning breakdown** (e.g., *"Invoice charges $175/unit instead of agreed $150/unit (+16.67% variance)"*), allowing human managers to resolve discrepancies 10x faster.

---

## 🏗️ System Architecture

The platform follows a decoupled architecture using a **LangGraph State Machine** embedded within a **FastAPI** backend, communicating asynchronously with a **React/Vite** dashboard via Server-Sent Events (SSE).

### Specialized Sub-Agents:
1. **Requisition Agent:** Validates PR completeness, checks budget allocations, and detects price outliers.
2. **Sourcing Agent:** Looks up internal vendor catalogs and performs Web Search fallbacks for reference pricing.
3. **Goods Receipt Agent:** Reconciles physical warehouse receiving against issued POs.
4. **Invoice 3-Way Matcher (Centerpiece):** Performs deep reconciliation, detects 4 classes of discrepancies, and halts the graph for human override if severity thresholds are crossed.

📚 **Detailed Architecture Docs:**
* [System & LangGraph Architecture](docs/02-architecture.md)
* [Database Schema & ERD](docs/03-database-schema.md)
* [REST API Specification](docs/04-api-spec.md)
* [Agent Evaluation & Benchmarking](docs/05-agent-evaluation.md)

---

## 🛠️ Quick Start (Local Development)

### Prerequisites
* Docker & Docker Compose
* `uv` (Python Package Manager)
* Node.js 20+ (for frontend)

### 1. Start the Database
```bash
docker-compose up -d
```

### 2. Backend Setup
```bash
cd backend
uv venv
source .venv/bin/activate
uv sync
alembic upgrade head
python -m app.db.seed
fastapi dev app/main.py
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 📊 Evaluation & Quality Benchmarks

The 3-Way Matcher agent is continuously evaluated against a synthetic dataset of 50 complex edge cases. We target **≥ 98.0% Recall** on high-severity financial discrepancies with a **< 2.0% False Positive Rate**.

See the [Agent Evaluation Framework](docs/05-agent-evaluation.md) for detailed metrics and the explainability scoring rubric.

---

## 🔐 Security & RBAC

Access is strictly governed by 5 roles: `Requester`, `Procurement Officer`, `Warehouse Staff`, `AP Clerk`, and `Finance Manager`. Human-in-the-loop overrides require cryptographic signatures in the append-only `audit_logs` table.

---

*Built with precision for modern enterprise procurement.*
