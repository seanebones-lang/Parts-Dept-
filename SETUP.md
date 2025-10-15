# Quick Setup Guide

## Prerequisites

1. **Docker & Docker Compose** installed
2. **Ollama** installed for local Llama 3
3. **Neo4j AuraDB** account (free tier works)
4. **Anthropic API key** for Claude
5. **Email account** with IMAP/SMTP enabled

## Step-by-Step Setup

### 1. Install Ollama and Pull Llama 3

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Pull Llama 3.2 model
ollama pull llama3.2
```

### 2. Create Neo4j AuraDB Instance

1. Go to https://neo4j.com/cloud/aura-free/
2. Sign up and create a free instance
3. Save the connection URI, username, and password
4. Wait for instance to be ready (2-3 minutes)

### 3. Get Anthropic API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key
5. Copy the key (starts with `sk-ant-`)

### 4. Configure Environment

Create `.env` file:

```bash
cd "/Users/seanmcdonnell/Desktop/Parts Dept"
cp .env.example .env
```

Edit `.env` with your actual credentials:

```env
# Neo4j (from AuraDB)
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password

# Ollama (local)
OLLAMA_BASE_URL=http://host.docker.internal:11434

# Anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Email (use Gmail with App Password)
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=your-email@gmail.com
IMAP_PASSWORD=your-app-password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=Parts Department <your-email@gmail.com>

# These are auto-configured by docker-compose
DATABASE_URL=postgresql://parts_dept:parts_dept_password@postgres:5432/parts_dept
REDIS_URL=redis://redis:6379/0
QDRANT_URL=http://qdrant:6333
```

### 5. Gmail App Password Setup

1. Enable 2-Factor Authentication on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Select "Mail" and your device
4. Generate password
5. Use this 16-character password in `.env`

### 6. Start the System

```bash
cd docker
docker-compose up -d

# Check all services are running
docker-compose ps

# Watch logs
docker-compose logs -f
```

Services will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Celery Flower: http://localhost:5555
- Qdrant Dashboard: http://localhost:6333/dashboard

### 7. Initialize Database

```bash
docker-compose exec api python -c "
from backend.database import init_db
import asyncio
asyncio.run(init_db())
print('Database initialized successfully')
"
```

### 8. Test the System

```bash
# Check health
curl http://localhost:8000/api/v1/health

# Should return: {"status":"healthy",...}
```

### 9. Create Sample Location

```bash
curl -X POST "http://localhost:8000/api/v1/inventory/locations" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "loc-001",
    "name": "Main Location",
    "address": "123 Main St",
    "city": "Springfield",
    "state": "IL",
    "zip_code": "62701",
    "phone": "555-0100",
    "email": "main@dealer.com"
  }'
```

### 10. Add Sample Parts

```bash
# Create brake pads part
curl -X POST "http://localhost:8000/api/v1/inventory/parts" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "BRK-001",
    "name": "Brake Pads - Front",
    "description": "Ceramic brake pads for most vehicles",
    "manufacturer": "Brembo",
    "category": "Brakes",
    "list_price": 89.99,
    "cost": 45.00
  }'

# Add to inventory
curl -X POST "http://localhost:8000/api/v1/inventory" \
  -H "Content-Type: application/json" \
  -d '{
    "location_id": "loc-001",
    "part_sku": "BRK-001",
    "quantity": 50,
    "min_stock": 10,
    "reorder_point": 15
  }'
```

### 11. Test Email Processing

```bash
curl -X POST "http://localhost:8000/api/v1/email/process" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Question about brake pads",
    "from_address": "customer@example.com",
    "body": "Do you have brake pads in stock? I need them for a Honda Civic."
  }'
```

## Verification Checklist

- [ ] Ollama running (`ollama list` shows llama3.2)
- [ ] Neo4j AuraDB accessible
- [ ] Docker containers all running (8 services)
- [ ] API responds at http://localhost:8000/health
- [ ] Can create locations via API
- [ ] Can create parts via API
- [ ] Email processing works
- [ ] Flower dashboard accessible at http://localhost:5555

## Common Issues

### "Cannot connect to Neo4j"

- Verify Neo4j AuraDB is running (check console)
- Check NEO4J_URI starts with `neo4j+s://`
- Ensure password is correct

### "Ollama connection refused"

- Start Ollama: `ollama serve`
- Check it's running: `curl http://localhost:11434/api/tags`
- Pull model if needed: `ollama pull llama3.2`

### "Email authentication failed"

- Use App Password, not regular password
- Enable "Less secure app access" (old Gmail accounts)
- Check IMAP/SMTP is enabled in email settings

### Docker containers keep restarting

```bash
# Check logs for specific service
docker-compose logs api
docker-compose logs worker

# Restart all services
docker-compose down
docker-compose up -d
```

## Next Steps

1. **Ingest Documents**: Add parts catalogs, FAQs, policies to vector store
2. **Configure Email Automation**: Enable auto-processing in Celery beat
3. **Add More Locations**: Create all 7-10 dealer locations
4. **Populate Inventory**: Import full parts catalog
5. **Test Order Flow**: Create orders and generate invoices
6. **Monitor**: Watch Flower dashboard for background tasks

## Production Deployment

For production deployment:
1. Use managed Neo4j AuraDB (not free tier)
2. Use Qdrant Cloud for vectors
3. Deploy to AWS ECS / GCP Cloud Run
4. Use managed PostgreSQL (RDS/Cloud SQL)
5. Use managed Redis (ElastiCache/Memorystore)
6. Set up proper monitoring (Prometheus/Grafana)
7. Enable HTTPS with load balancer
8. Implement rate limiting
9. Set up backup strategies

## Support

If you encounter issues:
1. Check logs: `docker-compose logs -f`
2. Verify `.env` configuration
3. Ensure all prerequisites are installed
4. Check network connectivity to external services

