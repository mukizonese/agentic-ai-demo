.PHONY: help build-local up-local up-prod down logs clean install-deps langflow-up langflow-up-apis langflow-up-full langflow-down langflow-logs langflow-clean langflow-health

# Default target
help:
	@echo "Agentic AI Demo - Available Commands:"
	@echo ""
	@echo "  make install-deps    - Install dependencies for all services"
	@echo "  make build-local     - Build all Docker images for local development"
	@echo "  make up-local        - Start services in local development mode"
	@echo "  make up-prod         - Start services in production mode"
	@echo "  make down           - Stop all services"
	@echo "  make logs           - Show logs from all services"
	@echo "  make logs-service   - Show logs from specific service (usage: make logs-service SERVICE=mcp-server)"
	@echo "  make clean          - Remove all containers, images, and volumes"
	@echo "  make health-check   - Check health of all services"
	@echo ""
	@echo "Langflow Commands (Integrated):"
	@echo "  make langflow-up     - Start all services including Langflow"
	@echo "  make langflow-up-apis - Start all services with Langflow"
	@echo "  make langflow-up-full - Start full stack with Langflow"
	@echo "  make langflow-down   - Stop all services including Langflow"
	@echo "  make langflow-logs   - Show all service logs"
	@echo "  make langflow-clean  - Clean up all containers and volumes"
	@echo "  make langflow-health - Check health of all services"
	@echo ""

# Install dependencies
install-deps:
	@echo "Setting up Python virtual environment..."
	@if [ ! -d ".venv" ]; then \
		python3.11 -m venv .venv; \
		echo "Created .venv virtual environment."; \
	fi
	@. .venv/bin/activate && \
	echo "Installing Python dependencies for backend services..." && \
	cd support-app-api && pip install -r requirements.txt && \
	cd ../product-app-api && pip install -r requirements.txt && \
	cd ../mcp-server && pip install -r requirements.txt && \
	echo "Installing Node.js dependencies for frontend..." && \
	cd ../frontend && npm install && \
	echo "Dependencies installed successfully!"

# Build all Docker images for local development
build-local:
	@echo "Building Docker images for local development..."
	docker-compose -f docker/docker-compose.local.yaml build --no-cache
	@echo "Build completed!"

# Start services in local development mode
up-local:
	@echo "Starting services in local development mode..."
	@echo "Make sure Ollama is running on your host machine (port 11434)"
	docker-compose -f docker/docker-compose.local.yaml up -d
	@echo ""
	@echo "Services are starting up..."
	@echo "Frontend: http://localhost:3000"
	@echo "MCP Server: http://localhost:8001"
	@echo "Support API: http://localhost:8003"
	@echo "Product API: http://localhost:8002"
	@echo "ChromaDB: http://localhost:8000"
	@echo "Langflow UI: http://localhost:7860"
	@echo ""
	@echo "Run 'make logs' to see startup logs"
	@echo "Run 'make health-check' to verify services are ready"

# Start services in production mode
up-prod:
	@echo "Starting services in production mode..."
	docker-compose -f docker/docker-compose.prod.yaml up -d
	@echo ""
	@echo "Services are starting up..."
	@echo "Frontend: http://localhost:3000"
	@echo "MCP Server: http://localhost:8000"
	@echo "Support API: http://localhost:8001"
	@echo "Product API: http://localhost:8002"
	@echo "ChromaDB: http://localhost:8000"
	@echo "Ollama: http://localhost:11434"
	@echo ""
	@echo "Run 'make logs' to see startup logs"
	@echo "Run 'make health-check' to verify services are ready"

# Stop all services
down:
	@echo "Stopping all services..."
	docker-compose -f docker/docker-compose.local.yaml down 2>/dev/null || true
	docker-compose -f docker/docker-compose.prod.yaml down 2>/dev/null || true
	@echo "All services stopped!"

# Restart all services in local development mode
restart:
	@echo "Restarting all services in local development mode..."
	$(MAKE) down
	$(MAKE) up-local
	@echo "All services restarted!"

# Show logs from all services
logs:
	@echo "Showing logs from all services (press Ctrl+C to exit)..."
	docker-compose -f docker/docker-compose.local.yaml logs -f 2>/dev/null || \
	docker-compose -f docker/docker-compose.prod.yaml logs -f

# Show logs from specific service
logs-service:
	@if [ -z "$(SERVICE)" ]; then \
		echo "Usage: make logs-service SERVICE=<service-name>"; \
		echo "Available services: mcp-server, frontend, support-app-api, product-app-api, chromadb, ollama"; \
		exit 1; \
	fi
	@echo "Showing logs for $(SERVICE)..."
	docker-compose -f docker/docker-compose.local.yaml logs -f $(SERVICE) 2>/dev/null || \
	docker-compose -f docker/docker-compose.prod.yaml logs -f $(SERVICE)

# Clean up everything
clean:
	@echo "Cleaning up Docker containers, images, and volumes..."
	docker-compose -f docker/docker-compose.local.yaml down -v --remove-orphans 2>/dev/null || true
	docker-compose -f docker/docker-compose.prod.yaml down -v --remove-orphans 2>/dev/null || true
	docker system prune -af --volumes
	@echo "Cleanup completed!"

# Health check for all services
health-check:
	@echo "Checking health of all services..."
	@echo ""
	@echo "Support API:"
	@curl -s http://localhost:8001/health | jq '.' 2>/dev/null || echo "Service not responding"
	@echo ""
	@echo "Product API:"
	@curl -s http://localhost:8002/health | jq '.' 2>/dev/null || echo "Service not responding"
	@echo ""
	@echo "MCP Server:"
	@curl -s http://localhost:8000/health | jq '.' 2>/dev/null || echo "Service not responding"
	@echo ""
	@echo "ChromaDB:"
	@curl -s http://localhost:8000/api/v1/heartbeat 2>/dev/null && echo "ChromaDB: Healthy" || echo "ChromaDB: Not responding"
	@echo ""

# Development helpers
dev-frontend:
	@echo "Starting frontend in development mode..."
	cd frontend && npm run dev

dev-mcp:
	@echo "Starting MCP server in development mode..."
	cd mcp-server && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-support:
	@echo "Starting Support API in development mode..."
	cd support-app-api && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001

dev-product:
	@echo "Starting Product API in development mode..."
	cd product-app-api && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8002

# Setup Ollama (for local development)
setup-ollama:
	@echo "Setting up Ollama for local development..."
	@echo "1. Install Ollama from https://ollama.ai"
	@echo "2. Pull the required model:"
	@echo "   ollama pull gemma:2b"
	@echo "3. Start Ollama service"
	@echo "4. Verify it's running: curl http://localhost:11434/api/tags"

# Langflow commands (integrated with main services)
langflow-up:
	@echo "Starting Langflow with integrated services..."
	$(MAKE) up-local
	@echo ""
	@echo "Langflow is starting up with all services..."
	@echo "Langflow UI: http://localhost:7860"
	@echo "Username: admin"
	@echo "Password: admin123"
	@echo "Frontend: http://localhost:3000"
	@echo "MCP Server: http://localhost:8001"
	@echo "Support API: http://localhost:8003"
	@echo "Product API: http://localhost:8002"
	@echo "ChromaDB: http://localhost:8000"
	@echo ""
	@echo "Run 'make logs' to see startup logs"

langflow-up-apis:
	@echo "Starting Langflow with APIs for testing..."
	$(MAKE) up-local
	@echo ""
	@echo "Langflow is starting up with APIs..."
	@echo "Langflow UI: http://localhost:7860"
	@echo "Support API: http://localhost:8003"
	@echo "Product API: http://localhost:8002"
	@echo ""
	@echo "Run 'make logs' to see startup logs"

langflow-up-full:
	@echo "Starting Langflow with full stack..."
	$(MAKE) up-local
	@echo ""
	@echo "Langflow is starting up with full stack..."
	@echo "Langflow UI: http://localhost:7860"
	@echo "Support API: http://localhost:8003"
	@echo "Product API: http://localhost:8002"
	@echo "ChromaDB: http://localhost:8000"
	@echo ""
	@echo "Run 'make logs' to see startup logs"

langflow-down:
	@echo "Stopping all services including Langflow..."
	$(MAKE) down
	@echo "All services stopped!"

langflow-logs:
	@echo "Showing all service logs including Langflow (press Ctrl+C to exit)..."
	$(MAKE) logs

langflow-clean:
	@echo "Cleaning up all containers and volumes including Langflow..."
	$(MAKE) clean
	@echo "All cleanup completed!"

langflow-health:
	@echo "Checking health of all services including Langflow..."
	@echo ""
	@echo "Langflow:"
	@curl -s http://localhost:7860/health 2>/dev/null && echo "Langflow: Healthy" || echo "Langflow: Not responding"
	@echo ""
	@echo "Support API:"
	@curl -s http://localhost:8003/health 2>/dev/null && echo "Support API: Healthy" || echo "Support API: Not responding"
	@echo ""
	@echo "Product API:"
	@curl -s http://localhost:8002/health 2>/dev/null && echo "Product API: Healthy" || echo "Product API: Not responding"
	@echo ""
	@echo "MCP Server:"
	@curl -s http://localhost:8001/health 2>/dev/null && echo "MCP Server: Healthy" || echo "MCP Server: Not responding"
	@echo ""
	@echo "ChromaDB:"
	@curl -s http://localhost:8000/api/v1/heartbeat 2>/dev/null && echo "ChromaDB: Healthy" || echo "ChromaDB: Not responding" 