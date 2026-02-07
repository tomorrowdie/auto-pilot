# Development Guide

## Getting Started

### Prerequisites

- Docker Desktop
- Git
- Code editor (VS Code recommended)

### Quick Start

1. **Clone and setup:**
   ```bash
   cd shopify-seo-analyzer
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start development environment:**
   ```bash
   # On Windows
   start-dev.bat
   
   # On Linux/Mac
   ./start-dev.sh
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Project Structure

```
shopify-seo-analyzer/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Configuration
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── tasks/          # Background tasks
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   └── services/       # API services
│   └── package.json        # Node dependencies
├── docker-compose.yml      # Development environment
└── .env.example           # Environment template
```

## Development Workflow

### Backend Development

1. **Add new dependencies:**
   ```bash
   # Add to requirements.txt, then rebuild
   docker-compose build backend
   ```

2. **Run tests:**
   ```bash
   docker-compose exec backend pytest
   ```

3. **Database migrations:**
   ```bash
   # Create migration
   docker-compose exec backend alembic revision --autogenerate -m "description"
   
   # Apply migration
   docker-compose exec backend alembic upgrade head
   ```

### Frontend Development

1. **Add new dependencies:**
   ```bash
   cd frontend
   npm install package-name
   # Rebuild container
   docker-compose build frontend
   ```

2. **Run tests:**
   ```bash
   docker-compose exec frontend npm test
   ```

## Implementation Tasks

Follow the tasks in `.kiro/specs/shopify-seo-analyzer/tasks.md`:

### ✅ Completed
- Task 1: Project foundation and development environment

### 🔄 Next Steps
- Task 2.1: Create SQLAlchemy base models and database configuration
- Task 2.2: Implement Store model with validation and relationships
- Task 2.3: Implement Product model with variants and SEO fields

## Useful Commands

### Docker Commands
```bash
# View logs
docker-compose logs -f [service_name]

# Restart service
docker-compose restart [service_name]

# Rebuild and restart
docker-compose up -d --build [service_name]

# Stop all services
docker-compose down

# Clean up
docker-compose down -v  # Remove volumes
docker system prune     # Clean up Docker
```

### Database Commands
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d shopify_seo

# Connect to Redis
docker-compose exec redis redis-cli
```

## Debugging

### Backend Debugging
- Logs: `docker-compose logs -f backend`
- Interactive shell: `docker-compose exec backend python`
- Database queries: Check logs with `echo=True` in database config

### Frontend Debugging
- Logs: `docker-compose logs -f frontend`
- Browser dev tools for React debugging
- Network tab for API calls

## Environment Variables

Key environment variables to configure:

```env
# Required for development
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/shopify_seo
REDIS_URL=redis://redis:6379

# Required for Shopify integration (Task 3)
SHOPIFY_API_KEY=your_key
SHOPIFY_API_SECRET=your_secret

# Required for AI features (Task 6)
OPENAI_API_KEY=your_key
```

## Next Implementation Steps

1. **Database Models (Task 2)**: Implement SQLAlchemy models
2. **Authentication (Task 3)**: Shopify OAuth integration
3. **Data Sync (Task 4)**: Shopify API integration
4. **SEO Analysis (Task 5)**: Core analysis engine
5. **AI Integration (Task 6)**: OpenAI content optimization

See the full task list in `.kiro/specs/shopify-seo-analyzer/tasks.md`