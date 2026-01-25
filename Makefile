# IEEE Paper Generator - Docker Commands

# Default environment file
ENV_FILE ?= .env

# Help command
.PHONY: help
help:
	@echo "IEEE Paper Generator - Docker Commands"
	@echo "======================================"
	@echo ""
	@echo "Production Commands:"
	@echo "  make build          - Build all Docker images"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View logs from all services"
	@echo "  make clean          - Remove all containers and volumes"
	@echo ""
	@echo "Development Commands:"
	@echo "  make dev-up         - Start development environment"
	@echo "  make dev-down       - Stop development environment"
	@echo "  make dev-logs       - View development logs"
	@echo "  make dev-clean      - Clean development environment"
	@echo ""
	@echo "Database Commands:"
	@echo "  make db-shell       - Connect to database shell"
	@echo "  make db-backup      - Backup database"
	@echo "  make db-restore     - Restore database"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make setup          - Initial setup (copy env files)"
	@echo "  make test           - Run tests"
	@echo "  make health         - Check service health"

# Setup commands
.PHONY: setup
setup:
	@echo "Setting up IEEE Paper Generator..."
	@if [ ! -f .env ]; then cp .env.docker .env; echo "Created .env file - please edit with your values"; fi
	@if [ ! -f frontend/.env ]; then cp frontend/.env.example frontend/.env; fi
	@echo "Setup complete! Edit .env files with your configuration."

# Production commands
.PHONY: build
build:
	@echo "Building Docker images..."
	docker-compose build --no-cache

.PHONY: up
up:
	@echo "Starting IEEE Paper Generator..."
	docker-compose --env-file $(ENV_FILE) up -d
	@echo "Services started! Frontend: http://localhost:3000, Backend: http://localhost:8000"

.PHONY: down
down:
	@echo "Stopping IEEE Paper Generator..."
	docker-compose down

.PHONY: restart
restart: down up

.PHONY: logs
logs:
	docker-compose logs -f

.PHONY: clean
clean:
	@echo "Cleaning up Docker resources..."
	docker-compose down -v --remove-orphans
	docker system prune -f

# Development commands
.PHONY: dev-up
dev-up:
	@echo "Starting development environment..."
	docker-compose -f docker-compose.dev.yml --env-file $(ENV_FILE) up -d
	@echo "Development environment started! Frontend: http://localhost:3001, Backend: http://localhost:8001"

.PHONY: dev-down
dev-down:
	@echo "Stopping development environment..."
	docker-compose -f docker-compose.dev.yml down

.PHONY: dev-logs
dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f

.PHONY: dev-clean
dev-clean:
	@echo "Cleaning development environment..."
	docker-compose -f docker-compose.dev.yml down -v --remove-orphans

# Database commands
.PHONY: db-shell
db-shell:
	docker-compose exec database psql -U postgres -d ieee_papers

.PHONY: db-backup
db-backup:
	@echo "Creating database backup..."
	docker-compose exec database pg_dump -U postgres ieee_papers > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backup created!"

.PHONY: db-restore
db-restore:
	@echo "Restoring database..."
	@read -p "Enter backup file path: " backup_file; \
	docker-compose exec -T database psql -U postgres ieee_papers < $$backup_file

# Utility commands
.PHONY: test
test:
	@echo "Running backend tests..."
	docker-compose exec backend python test_setup.py

.PHONY: health
health:
	@echo "Checking service health..."
	@echo "Frontend: $$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/health || echo 'DOWN')"
	@echo "Backend: $$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/ || echo 'DOWN')"
	@echo "Database: $$(docker-compose exec database pg_isready -U postgres -d ieee_papers || echo 'DOWN')"

# Individual service commands
.PHONY: backend-shell
backend-shell:
	docker-compose exec backend /bin/bash

.PHONY: frontend-shell
frontend-shell:
	docker-compose exec frontend /bin/sh

.PHONY: backend-logs
backend-logs:
	docker-compose logs -f backend

.PHONY: frontend-logs
frontend-logs:
	docker-compose logs -f frontend

.PHONY: db-logs
db-logs:
	docker-compose logs -f database