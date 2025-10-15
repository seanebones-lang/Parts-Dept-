# Installation Guide

## Quick Install (Recommended)

The easiest way to run this system is with Docker, which handles all dependencies automatically.

### Option 1: Docker (Recommended)

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 2. Start all services
cd docker
docker-compose up -d

# 3. Initialize database
docker-compose exec api python -c "
from backend.database import init_db
import asyncio
asyncio.run(init_db())
"

# 4. Seed sample data
docker-compose exec api python scripts/seed_data.py
```

That's it! Services will be available at:
- API: http://localhost:8000/docs
- Celery: http://localhost:5555

## Option 2: Local Installation (Development)

For local development without Docker:

### Prerequisites

- Python 3.9+
- PostgreSQL running locally
- Redis running locally
- Neo4j AuraDB account (or local Neo4j)
- Qdrant running locally (or Qdrant Cloud)
- Ollama installed with Llama 3

### Installation Steps

1. **Run the install script:**

```bash
./install.sh
```

This will:
- Create a virtual environment
- Upgrade pip
- Install all dependencies
- Handle version conflicts automatically

2. **Activate virtual environment:**

```bash
source venv/bin/activate
```

3. **Configure environment:**

```bash
cp .env.example .env
# Edit .env with your credentials
```

4. **Start services manually:**

```bash
# Terminal 1: API
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Celery Worker
celery -A backend.workers.celery_app worker --loglevel=info

# Terminal 3: Celery Beat (scheduler)
celery -A backend.workers.celery_app beat --loglevel=info
```

## Dependency Issues

If you encounter dependency conflicts:

1. **Use minimal requirements:**

```bash
pip install -r requirements-minimal.txt
```

2. **Install problematic packages separately:**

```bash
pip install fastapi uvicorn neo4j qdrant-client anthropic
```

3. **Use Docker** (avoids all local dependency issues)

## System Requirements

### For Docker Installation:
- Docker Desktop (macOS/Windows) or Docker Engine (Linux)
- 4GB RAM minimum
- 10GB disk space

### For Local Installation:
- Python 3.9 or higher
- PostgreSQL 14+
- Redis 7+
- 4GB RAM minimum
- 10GB disk space

## Verify Installation

Test that everything works:

```bash
# With Docker
docker-compose exec api python test_build.py

# Without Docker (in venv)
python test_build.py
```

## Troubleshooting

### Pip Version Error

If you see pip version warnings:

```bash
# In virtual environment
pip install --upgrade pip
```

### Permission Denied

If you get permission errors with system Python:

```bash
# Always use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Dependency Conflicts

If langchain or litellm cause conflicts:

```bash
# Use minimal requirements (removes langchain/litellm)
pip install -r requirements-minimal.txt
```

The system will work fine without these as we use direct API calls.

### WeasyPrint Installation Issues

WeasyPrint requires system libraries. If it fails:

**macOS:**
```bash
brew install cairo pango gdk-pixbuf libffi
```

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

**Or use Docker** (recommended to avoid system dependency issues)

## Development Workflow

1. **Make changes to code**
2. **Test locally:**
   ```bash
   python test_build.py
   ```

3. **Run with Docker:**
   ```bash
   cd docker
   docker-compose up --build
   ```

## Production Deployment

For production, use Docker deployment:

1. **Build production image:**
   ```bash
   docker build -f docker/Dockerfile -t parts-dept:latest .
   ```

2. **Deploy to cloud:**
   - AWS ECS: Use task definition with the image
   - GCP Cloud Run: Deploy container directly
   - Kubernetes: Use deployment YAML

See README.md for detailed production deployment instructions.

## Getting Help

If installation fails:

1. Check logs: `docker-compose logs -f`
2. Verify `.env` configuration
3. Ensure all external services are accessible (Neo4j, etc.)
4. Run build test: `python test_build.py`
5. Use minimal requirements if needed

## Next Steps

After successful installation:

1. Read SETUP.md for system configuration
2. Run seed_data.py to populate sample data
3. Access API docs at http://localhost:8000/docs
4. Configure email automation
5. Set up Neo4j with your inventory data

