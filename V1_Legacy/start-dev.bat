@echo off
REM Shopify SEO Analyzer - Development Startup Script for Windows

echo 🚀 Starting Shopify SEO Analyzer Development Environment...

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker and try again.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ✅ .env file created. Please edit it with your configuration.
)

REM Build and start services
echo 🔨 Building and starting services...
docker-compose up -d --build

REM Wait for services to be ready
echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak >nul

echo.
echo 🎉 Development environment is starting up!
echo.
echo 📱 Access points:
echo    Frontend:  http://localhost:3000
echo    Backend:   http://localhost:8000
echo    API Docs:  http://localhost:8000/docs
echo.
echo 📊 Monitoring:
echo    Logs:      docker-compose logs -f
echo    Status:    docker-compose ps
echo.
echo 🛑 To stop:
echo    docker-compose down
echo.

REM Show logs
echo 📋 Showing recent logs (Ctrl+C to exit):
docker-compose logs -f --tail=50