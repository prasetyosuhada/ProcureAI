.PHONY: help install install-backend install-frontend up down logs dev-backend dev-frontend migrate seed db-reset test test-verbose eval build-frontend check clean

# Colors for terminal output
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RESET := \033[0m

help: ## Show this help message
	@echo ""
	@echo "  $(CYAN)🛒 ProcureAI Development Commands$(RESET)"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-18s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""

# ==========================================
# 📦 Installation & Setup
# ==========================================
install: install-backend install-frontend ## Install all dependencies (backend & frontend)

install-backend: ## Install Python dependencies with uv
	@echo "$(YELLOW)Installing backend dependencies...$(RESET)"
	cd backend && uv sync

install-frontend: ## Install Node.js dependencies
	@echo "$(YELLOW)Installing frontend dependencies...$(RESET)"
	cd frontend && npm install

# ==========================================
# 🐳 Docker Infrastructure
# ==========================================
up: ## Start PostgreSQL and Redis containers in background
	@echo "$(GREEN)Starting PostgreSQL & Redis containers...$(RESET)"
	docker compose up -d

down: ## Stop Docker containers
	@echo "$(YELLOW)Stopping Docker containers...$(RESET)"
	docker compose down

logs: ## View live Docker container logs
	docker compose logs -f

# ==========================================
# 🗄️ Database Migrations, Seeding & Reset
# ==========================================
migrate: ## Run Alembic database migrations
	@echo "$(GREEN)Applying database migrations...$(RESET)"
	cd backend && uv run alembic upgrade head

seed: ## Seed enterprise data into database (inventory, assets, budgets, pipeline)
	@echo "$(GREEN)Seeding enterprise dataset into PostgreSQL...$(RESET)"
	cd backend && uv run python -m app.db.seed

db-reset: ## Reset database volumes, apply migrations and seed data
	@echo "$(YELLOW)Resetting database volumes and starting fresh containers...$(RESET)"
	docker compose down -v
	docker compose up -d
	@sleep 2
	@echo "$(GREEN)Applying migrations...$(RESET)"
	cd backend && uv run alembic upgrade head
	@echo "$(GREEN)Seeding enterprise data...$(RESET)"
	cd backend && uv run python -m app.db.seed
	@echo "$(GREEN)Database reset and seeded successfully!$(RESET)"

# ==========================================
# 🚀 Development Servers
# ==========================================
dev-backend: ## Start FastAPI development server (port 8000)
	@echo "$(GREEN)Starting FastAPI backend on http://localhost:8000...$(RESET)"
	cd backend && uv run uvicorn main:app --reload --port 8000

dev-frontend: ## Start Vite React development server (port 5173)
	@echo "$(GREEN)Starting React frontend on http://localhost:5173...$(RESET)"
	cd frontend && npm run dev

# ==========================================
# 🧪 Testing & Evaluation
# ==========================================
test: ## Run full backend pytest test suite
	@echo "$(GREEN)Running backend pytest suite...$(RESET)"
	cd backend && uv run pytest

test-verbose: ## Run pytest with verbose details
	cd backend && uv run pytest -vv

eval: ## Run Golden Dataset & LLM-as-a-Judge evaluation suite
	@echo "$(CYAN)Running AI agent evaluation suite...$(RESET)"
	cd backend && uv run python -m app.eval.run_eval

build-frontend: ## Build frontend production bundle
	@echo "$(YELLOW)Building frontend distribution...$(RESET)"
	cd frontend && npm run build

check: test build-frontend ## Run all test suites and verify frontend build
	@echo "$(GREEN)All health and verification checks passed!$(RESET)"

# ==========================================
# 🧹 Cleanup
# ==========================================
clean: ## Clean cache files and build artifacts
	@echo "$(YELLOW)Cleaning temporary files...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/dist 2>/dev/null || true
	@echo "$(GREEN)Cleanup completed.$(RESET)"
