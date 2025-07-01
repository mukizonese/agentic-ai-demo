# Agentic AI Demo

A multi-agent AI demonstration project featuring FastAPI, LangChain, React, and Docker orchestration with support for multiple LLM backends and vector databases.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)
- Make (optional, for convenience commands)

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd agentic-ai-demo
```

### 2. Choose Your Deployment Mode

#### Option A: Local Development (Recommended for development)

Requires Ollama running on your host machine:

```bash
# Install and start Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull gemma:2b
ollama serve

# Start the services
make up-local
```

#### Option B: Production Mode (Self-contained)

Includes Ollama in Docker containers:

```bash
make up-prod
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **MCP Server**: http://localhost:8000
- **Support API**: http://localhost:8001
- **Product API**: http://localhost:8002

## 🏗️ Architecture

```
Frontend (React + Tailwind)
   │
   ▼
MCP Server (FastAPI + LangChain)
 ┌────────────────────┬────────────────────┬────────────────────┐
 │ Support App Agent   │ Product App Agent   │ Knowledge Agent    │
 │ (calls Support App) │ (calls Product App) │ (RAG: Vector DB)   │
 └────────────────────┴────────────────────┴────────────────────┘
   │                    │                    │
Support App API    Product App API    ChromaDB/Pinecone + LLM
```

## 📁 Project Structure

```
agentic-ai-demo/
├── frontend/                   # React + Tailwind TypeScript app
│   ├── src/
│   │   ├── app/               # Next.js app directory
│   │   ├── components/        # React components
│   │   ├── contexts/          # React contexts
│   │   ├── lib/              # Utilities and API client
│   │   └── types/            # TypeScript definitions
│   ├── Dockerfile            # Development container
│   └── Dockerfile.prod       # Production container
├── mcp-server/                # Multi-agent orchestration server
│   ├── agents/               # Agent implementations
│   ├── services/             # LLM and vector services
│   └── main.py              # FastAPI application
├── support-app-api/          # Mock Support App
├── product-app-api/          # Mock Product App
├── docker/                   # Docker configurations
│   ├── docker-compose.local.yaml
│   ├── docker-compose.prod.yaml
│   └── env/                 # Environment files
└── Makefile                 # Convenience commands
```

## 🔧 Configuration

### Environment Variables

The system supports multiple LLM and vector database backends through environment variables:

#### LLM Backend Selection
```env
USE_OLLAMA=true          # Use local Ollama
USE_OPENAI=false         # Use OpenAI API
USE_HF=false            # Use HuggingFace API
```

#### Vector Database Selection
```env
USE_PINECONE_API=false      # Use Pinecone cloud
USE_LOCAL_VECTORDB=true     # Use local ChromaDB
LOCAL_VECTORDB_TYPE=chroma  # Local vector DB type
```

#### Model Configuration
```env
OLLAMA_MODEL=gemma:2b
OPENAI_MODEL=gpt-3.5-turbo
HF_MODEL=microsoft/DialoGPT-medium
```

### Configuration Files

- **Local Development**: `docker/env/.env.docker_local`
- **Production**: `docker/env/.env.prod`

## 🤖 Agents

### Support Agent
- Handles support-related queries
- Fetches data from Support App API
- Enriches responses with LLM-generated content

### Product Agent
- Processes product information requests
- Integrates with Product App API
- Provides product recommendations and comparisons

### Knowledge Agent
- Performs RAG (Retrieval-Augmented Generation)
- Uses vector database for similarity search
- Combines retrieved context with LLM responses

## 🛠️ Available Commands

```bash
# Setup and Installation
make install-deps       # Install all dependencies
make setup-ollama       # Setup instructions for Ollama

# Docker Operations
make build-local        # Build images for local development
make up-local          # Start local development environment
make up-prod           # Start production environment
make down              # Stop all services
make clean             # Remove all containers and volumes

# Monitoring and Debugging
make logs              # Show logs from all services
make logs-service SERVICE=mcp-server  # Show specific service logs
make health-check      # Check health of all services

# Development
make dev-frontend      # Run frontend in dev mode
make dev-mcp          # Run MCP server in dev mode
make dev-support      # Run Support API in dev mode
make dev-product      # Run Product API in dev mode
```

## 🔍 API Endpoints

### MCP Server (Port 8000)
- `POST /chat` - Main chat interface
- `GET /health` - Health check
- `GET /config` - Current configuration
- `GET /agents/status` - Agent status

### Support App API (Port 8001)
- `GET /support_articles` - All support articles
- `GET /support_articles/{id}` - Specific article
- `GET /support_articles/search/{query}` - Search articles

### Product App API (Port 8002)
- `GET /products` - All products
- `GET /products/{id}` - Specific product
- `GET /products/search/{query}` - Search products
- `GET /products/category/{category}` - Products by category

## 🌐 Frontend Features

- **Modern Chat Interface**: Clean, responsive design with Tailwind CSS
- **Agent Response Display**: Shows which agents responded and processing times
- **Real-time Updates**: Live chat with typing indicators
- **Mobile Responsive**: Works on all device sizes
- **Error Handling**: Graceful error display and recovery

## 🔧 Development

### Local Development Setup

1. **Backend Services**:
```bash
# Terminal 1 - Support API
cd support-app-api
pip install -r requirements.txt
python main.py

# Terminal 2 - Product API
cd product-app-api
pip install -r requirements.txt
python main.py

# Terminal 3 - MCP Server
cd mcp-server
pip install -r requirements.txt
python main.py
```

2. **Frontend**:
```bash
# Terminal 4 - Frontend
cd frontend
npm install
npm run dev
```

3. **ChromaDB** (Optional):
```bash
docker run -p 8000:8000 chromadb/chroma:latest
```

### Adding New Agents

1. Create agent class in `mcp-server/agents/`
2. Implement `process_query` method
3. Register in `mcp-server/main.py` orchestrator

### Customizing LLM Backends

1. Update environment variables
2. Modify `mcp-server/services/llm_service.py`
3. Add new backend implementation

## 🚀 Deployment

### Production Deployment

The system is designed for easy deployment on VPS or cloud platforms:

```bash
# Clone on your server
git clone <your-repo-url>
cd agentic-ai-demo

# Start production environment
make up-prod

# Monitor services
make health-check
make logs
```

### Docker Compose Profiles

- **Local**: Uses host Ollama, development containers
- **Production**: Includes Ollama container, optimized builds

## 🔍 Troubleshooting

### Common Issues

1. **Services not starting**:
   ```bash
   make health-check
   make logs
   ```

2. **Ollama connection issues**:
   ```bash
   curl http://localhost:11434/api/tags
   ollama list
   ```

3. **Frontend build issues**:
   ```bash
   cd frontend
   npm install
   npm run build
   ```

4. **ChromaDB connection issues**:
   ```bash
   docker logs chromadb
   ```

### Port Conflicts

If you have port conflicts, modify the ports in the Docker Compose files:
- Frontend: 3000
- MCP Server: 8000
- Support API: 8001
- Product API: 8002
- ChromaDB: 8000 (internal)
- Ollama: 11434

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

If you encounter any issues or have questions:

1. Check the troubleshooting section
2. Review the logs: `make logs`
3. Create an issue on GitHub
4. Check agent status: `make health-check`
