#!/bin/bash

echo "======================================"
echo "Parts Department System - Quick Start"
echo "======================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please create .env from .env.example and configure your credentials"
    exit 1
fi

echo "✓ .env file found"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

echo "✓ Docker is running"

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama not detected at localhost:11434"
    echo "Make sure Ollama is running: ollama serve"
    echo "And pull the model: ollama pull llama3.2"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ Ollama is running"
fi

echo ""
echo "Starting services..."
cd docker
docker-compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

echo ""
echo "Initializing database..."
docker-compose exec -T api python -c "
from backend.database import init_db
import asyncio
asyncio.run(init_db())
print('✓ Database initialized')
" 2>/dev/null

echo ""
echo "======================================"
echo "System is ready!"
echo "======================================"
echo ""
echo "Services available at:"
echo "  • API:            http://localhost:8000"
echo "  • API Docs:       http://localhost:8000/docs"
echo "  • Celery Flower:  http://localhost:5555"
echo "  • Qdrant:         http://localhost:6333/dashboard"
echo ""
echo "Next steps:"
echo "  1. Seed sample data: docker-compose exec api python scripts/seed_data.py"
echo "  2. Test system:      docker-compose exec api python scripts/test_system.py"
echo "  3. View logs:        docker-compose logs -f"
echo ""
echo "To stop: cd docker && docker-compose down"
echo ""

