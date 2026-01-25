# IEEE Paper Generator - Docker Setup

## 🐳 Quick Start

### Prerequisites
- Docker Desktop installed
- Docker Compose v2.0+
- At least 4GB RAM available for Docker

### 1. Initial Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd Research_Paper_Gen

# Setup environment files
make setup
# OR manually:
cp .env.docker .env
cp frontend/.env.example frontend/.env
```

### 2. Configure Environment
Edit `.env` file with your API keys:
```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional (for external Supabase)
SUPABASE_KEY=your_supabase_key

# Database password
DB_PASSWORD=your_secure_password
```

### 3. Start the Application
```bash
# Production mode
make up

# Development mode (with hot reload)
make dev-up
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Database**: localhost:5432

## 🚀 Docker Services

### Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Frontend     │    │     Backend     │    │    Database     │
│   (React/Vite)  │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL)   │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │     Redis       │
                    │   (Caching)     │
                    │   Port: 6379    │
                    └─────────────────┘
```

### Services Overview

#### 🎨 Frontend (React + Vite + Nginx)
- **Image**: Custom built from Node.js
- **Port**: 3000 (production), 3001 (development)
- **Features**: 
  - Optimized production build
  - Nginx reverse proxy
  - Static asset caching
  - Gzip compression

#### ⚡ Backend (FastAPI + Python)
- **Image**: Custom built from Python 3.11
- **Port**: 8000 (production), 8001 (development)
- **Features**:
  - AI-powered paper generation
  - File upload handling
  - Vector embeddings with all-MiniLM-L6-v2
  - RESTful API with automatic docs

#### 🗄️ Database (PostgreSQL + pgvector)
- **Image**: pgvector/pgvector:pg15
- **Port**: 5432 (production), 5433 (development)
- **Features**:
  - Vector similarity search
  - Automatic schema initialization
  - Data persistence

#### 🚀 Redis (Optional Caching)
- **Image**: redis:7-alpine
- **Port**: 6379
- **Features**:
  - Session caching
  - API response caching
  - Rate limiting support

## 📋 Available Commands

### Production Commands
```bash
make build          # Build all Docker images
make up             # Start all services
make down           # Stop all services
make restart        # Restart all services
make logs           # View logs from all services
make clean          # Remove all containers and volumes
```

### Development Commands
```bash
make dev-up         # Start development environment
make dev-down       # Stop development environment
make dev-logs       # View development logs
make dev-clean      # Clean development environment
```

### Database Commands
```bash
make db-shell       # Connect to database shell
make db-backup      # Backup database
make db-restore     # Restore database
```

### Utility Commands
```bash
make setup          # Initial setup (copy env files)
make test           # Run tests
make health         # Check service health
```

## 🔧 Configuration

### Environment Variables

#### Backend Configuration
```bash
# Database
SUPABASE_URL=postgresql://postgres:password@database:5432/ieee_papers
SUPABASE_KEY=optional_for_external_supabase

# AI API
GEMINI_API_KEY=your_gemini_api_key

# App Settings
DEBUG=false
APP_NAME=IEEE Paper Generator
MAX_FILE_SIZE=10485760
UPLOAD_DIR=uploads

# RAG Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RESULTS=5

# Generation Settings
MAX_TOKENS=2000
TEMPERATURE=0.7

# Embedding Settings
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
```

#### Frontend Configuration
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=IEEE Paper Generator
VITE_MAX_FILE_SIZE=10485760
VITE_ALLOWED_FILE_TYPES=.pdf,.docx
```

### Volume Mounts
- `postgres_data`: Database persistence
- `backend_uploads`: Uploaded files storage
- `backend_models`: AI model cache
- `redis_data`: Redis persistence

## 🛠️ Development Workflow

### Hot Reload Development
```bash
# Start development environment
make dev-up

# View logs
make dev-logs

# The application will automatically reload on code changes
```

### Debugging
```bash
# Access backend shell
make backend-shell

# Access database shell
make db-shell

# View specific service logs
make backend-logs
make frontend-logs
make db-logs
```

### Testing
```bash
# Run backend tests
make test

# Check service health
make health
```

## 🚀 Production Deployment

### Docker Swarm (Recommended)
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml ieee-paper-gen
```

### Kubernetes
```bash
# Convert docker-compose to k8s manifests
kompose convert

# Apply to cluster
kubectl apply -f .
```

### Cloud Deployment
- **AWS**: Use ECS with the provided docker-compose.yml
- **Google Cloud**: Deploy to Cloud Run or GKE
- **Azure**: Use Container Instances or AKS

## 📊 Monitoring & Logging

### Health Checks
All services include health checks:
- **Frontend**: HTTP GET to `/health`
- **Backend**: HTTP GET to `/`
- **Database**: `pg_isready` command
- **Redis**: `redis-cli ping`

### Log Management
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f database
```

### Metrics Collection
Consider adding:
- Prometheus for metrics
- Grafana for visualization
- ELK stack for log analysis

## 🔒 Security Considerations

### Production Security
1. **Environment Variables**: Never commit real API keys
2. **Database**: Use strong passwords and limit connections
3. **Network**: Use Docker networks for service isolation
4. **SSL/TLS**: Add HTTPS termination (nginx-proxy or Traefik)
5. **Secrets**: Use Docker secrets for sensitive data

### Recommended Security Headers
Already included in nginx.conf:
- X-Frame-Options
- X-XSS-Protection
- X-Content-Type-Options
- Referrer-Policy
- Content-Security-Policy

## 🐛 Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check what's using the port
netstat -tulpn | grep :3000

# Use different ports
docker-compose -f docker-compose.dev.yml up
```

#### Database Connection Issues
```bash
# Check database health
make health

# Reset database
make clean
make up
```

#### Memory Issues
```bash
# Check Docker memory usage
docker stats

# Increase Docker memory limit in Docker Desktop
```

#### Model Download Issues
```bash
# Pre-download models
docker-compose exec backend python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### Performance Optimization

#### Backend Optimization
- Increase worker processes for production
- Use Redis for caching
- Optimize database queries
- Use connection pooling

#### Frontend Optimization
- Enable gzip compression (already configured)
- Use CDN for static assets
- Implement service worker for caching
- Optimize bundle size

## 📈 Scaling

### Horizontal Scaling
```bash
# Scale backend service
docker-compose up -d --scale backend=3

# Use load balancer (nginx, HAProxy, or cloud LB)
```

### Database Scaling
- Read replicas for PostgreSQL
- Connection pooling with PgBouncer
- Database sharding for large datasets

### Caching Strategy
- Redis for session storage
- Application-level caching
- CDN for static assets
- Database query caching

## 🔄 Backup & Recovery

### Database Backup
```bash
# Automated backup
make db-backup

# Manual backup
docker-compose exec database pg_dump -U postgres ieee_papers > backup.sql
```

### Volume Backup
```bash
# Backup volumes
docker run --rm -v ieee_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

### Disaster Recovery
1. Regular automated backups
2. Test restore procedures
3. Monitor backup integrity
4. Document recovery procedures