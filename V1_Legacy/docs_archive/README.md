# Shopify SEO Analyzer & Optimizer

A comprehensive SEO analysis and optimization tool for Shopify stores, featuring AI-powered content suggestions, competitive analysis, and automated technical SEO monitoring.

## Project Structure

```
shopify-seo-analyzer/
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── api/            # API routes and endpoints
│   │   ├── core/           # Core configuration and settings
│   │   ├── models/         # SQLAlchemy database models
│   │   ├── services/       # Business logic services
│   │   ├── tasks/          # Celery background tasks
│   │   └── utils/          # Utility functions
│   ├── tests/              # Backend tests
│   ├── alembic/            # Database migrations
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile         # Backend container
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API client services
│   │   ├── hooks/          # Custom React hooks
│   │   ├── types/          # TypeScript type definitions
│   │   └── utils/          # Frontend utilities
│   ├── public/             # Static assets
│   ├── package.json        # Node.js dependencies
│   └── Dockerfile         # Frontend container
├── docker-compose.yml      # Development environment
├── .env.example           # Environment variables template
└── docs/                  # Project documentation
```

## Quick Start

1. Clone and setup:
```bash
cd shopify-seo-analyzer
cp .env.example .env
# Edit .env with your configuration
```

2. Start development environment:
```bash
docker-compose up -d
```

3. Run database migrations:
```bash
docker-compose exec backend alembic upgrade head
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Development

This project follows a modern full-stack architecture with:
- **Backend**: FastAPI with SQLAlchemy and Celery
- **Frontend**: React with TypeScript and Tailwind CSS
- **Database**: PostgreSQL with Redis for caching
- **Development**: Docker Compose for local development

## Next Steps

1. Configure environment variables in `.env`
2. Set up Shopify Partner account and app
3. Configure external API keys (OpenAI, Google, etc.)
4. Run the development environment
5. Start implementing features following the task list

For detailed implementation guidance, see the spec files in `.kiro/specs/shopify-seo-analyzer/`.