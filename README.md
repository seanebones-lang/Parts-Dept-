# Parts Department System

Enterprise-grade RAG + Graph system for auto dealer operations with 7-10 locations. Combines Neo4j graph database for inventory management with RAG (Retrieval Augmented Generation) for intelligent email routing, customer interaction, order processing, and invoice automation.

## Architecture

### Core Technologies (October 2025 - Current Stack)

- **Backend**: FastAPI 0.115+ (Python 3.11+)
- **Graph Database**: Neo4j 5.26+ (cloud-native AuraDB)
- **Vector Store**: Qdrant 1.12+ for RAG embeddings
- **LLMs**: Multi-model routing (October 2025)
  - Llama 3.2 (fast, local via Ollama 0.4+)
  - Claude 3.5 Sonnet (best reasoning, Anthropic)
  - Mistral Large 24.07 (balanced, cost-effective)
- **Email**: IMAP/SMTP with async processing (aiosmtplib 3.0+)
- **Task Queue**: Celery 5.4+ with Redis 7+
- **Relational DB**: PostgreSQL 16+ with asyncpg 0.30+
- **Containerization**: Docker 24+ / Docker Compose 2.23+
- **Embeddings**: Sentence Transformers 3.3+ (all-MiniLM-L6-v2, BGE, GTE)

### System Features

1. **Multi-Location Inventory Management** (Graph)
   - Real-time inventory tracking across 7-10 locations
   - Cross-location transfer capabilities
   - Low stock monitoring and alerts
   - Supplier relationship tracking

2. **Intelligent Email Processing** (RAG)
   - Automatic intent classification
   - Smart routing to departments
   - Context-aware response generation
   - Human-in-the-loop for low-confidence scenarios

3. **Order & Invoice Automation**
   - Automated order processing
   - PDF invoice generation
   - Email delivery with attachments
   - Payment integration ready (Stripe/Square)

4. **Background Workers**
   - Scheduled inbox processing (every 5 minutes)
   - Daily low stock reports
   - Async email sending
   - Invoice generation queue

## Project Structure

```
Parts Dept/
├── backend/
│   ├── api/              # FastAPI routes
│   │   ├── health.py
│   │   ├── inventory.py
│   │   ├── orders.py
│   │   └── email_routes.py
│   ├── graph/            # Neo4j graph database
│   │   ├── connection.py
│   │   ├── schema.py
│   │   └── queries.py
│   ├── rag/              # RAG system
│   │   ├── vectorstore.py
│   │   ├── ingestion.py
│   │   └── retrieval.py
│   ├── llm/              # Multi-model LLM router
│   │   └── router.py
│   ├── email/            # Email processing
│   │   ├── imap_listener.py
│   │   ├── smtp_sender.py
│   │   └── processor.py
│   ├── invoice/          # PDF invoice generation
│   │   └── generator.py
│   ├── workers/          # Celery background tasks
│   │   ├── celery_app.py
│   │   └── tasks.py
│   ├── config.py         # Configuration management
│   ├── database.py       # PostgreSQL connection
│   ├── models.py         # SQLAlchemy models
│   └── main.py           # FastAPI application
├── docker/               # Docker configurations
│   ├── Dockerfile
│   └── docker-compose.yml
├── requirements.txt
└── README.md
```

## Setup Instructions

### Prerequisites

- Docker & Docker Compose
- Neo4j AuraDB account (or local Neo4j instance)
- Ollama installed (for local Llama 3)
- Anthropic API key (for Claude)
- Email account with IMAP/SMTP access

### 1. Environment Configuration

Create `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Neo4j (get from AuraDB or use local instance)
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# LLM APIs
ANTHROPIC_API_KEY=sk-ant-xxxxx
MISTRAL_API_KEY=xxxxx  # Optional

# Email Configuration
IMAP_HOST=imap.gmail.com
IMAP_USER=your-email@company.com
IMAP_PASSWORD=your-app-password
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@company.com
SMTP_PASSWORD=your-app-password

# Database (provided by docker-compose)
DATABASE_URL=postgresql://parts_dept:parts_dept_password@postgres:5432/parts_dept

# Redis (provided by docker-compose)
REDIS_URL=redis://redis:6379/0
```

### 2. Start Ollama (for Llama 3)

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh

# Pull Llama 3 model
ollama pull llama3.2
```

### 3. Launch the System

```bash
# Build and start all services
cd docker
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### 4. Initialize the Database

```bash
# Run database migrations
docker-compose exec api python -c "
from backend.database import init_db
import asyncio
asyncio.run(init_db())
"
```

### 5. Seed Initial Data (Optional)

```bash
# Create sample locations and parts via API
curl -X POST "http://localhost:8000/api/v1/inventory/locations" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "loc-001",
    "name": "Main Street Location",
    "address": "123 Main St",
    "city": "Springfield",
    "state": "IL",
    "zip_code": "62701",
    "phone": "555-0100",
    "email": "mainstreet@dealer.com"
  }'
```

## API Documentation

Once running, access interactive API docs:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Celery Flower** (task monitoring): http://localhost:5555

## Key Endpoints

### Health & Status
- `GET /api/v1/health` - Health check
- `GET /api/v1/ready` - Readiness check

### Inventory Management
- `POST /api/v1/inventory/locations` - Create location
- `GET /api/v1/inventory/locations` - List all locations
- `POST /api/v1/inventory/parts` - Create part
- `POST /api/v1/inventory` - Add inventory to location
- `GET /api/v1/inventory/check/{sku}` - Check inventory
- `GET /api/v1/inventory/low-stock` - Get low stock items
- `POST /api/v1/inventory/transfer` - Transfer between locations
- `GET /api/v1/inventory/parts/search?q=brake` - Search parts

### Orders & Invoices
- `POST /api/v1/orders` - Create order
- `GET /api/v1/orders/{order_id}` - Get order details
- `POST /api/v1/orders/{order_id}/invoice` - Generate invoice
- `POST /api/v1/orders/{order_id}/invoice/send` - Email invoice

### Email Processing
- `POST /api/v1/email/process` - Process single email
- `POST /api/v1/email/send` - Send email
- `GET /api/v1/email/fetch` - Fetch unread emails
- `POST /api/v1/email/process-inbox` - Process inbox batch
- `GET /api/v1/email/logs` - View email processing logs

## Usage Examples

### 1. Create a Complete Location

```bash
curl -X POST "http://localhost:8000/api/v1/inventory/locations" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "loc-downtown",
    "name": "Downtown Service Center",
    "address": "456 Oak Avenue",
    "city": "Springfield",
    "state": "IL",
    "zip_code": "62702",
    "phone": "555-0200",
    "email": "downtown@dealer.com",
    "manager": "John Smith"
  }'
```

### 2. Add Parts to Inventory

```bash
# Create part
curl -X POST "http://localhost:8000/api/v1/inventory/parts" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "BRK-PAD-001",
    "name": "Ceramic Brake Pads",
    "description": "High-performance ceramic brake pads",
    "manufacturer": "Brembo",
    "category": "Brakes",
    "list_price": 89.99,
    "cost": 45.00
  }'

# Add to location inventory
curl -X POST "http://localhost:8000/api/v1/inventory" \
  -H "Content-Type: application/json" \
  -d '{
    "location_id": "loc-downtown",
    "part_sku": "BRK-PAD-001",
    "quantity": 50,
    "min_stock": 10,
    "reorder_point": 15
  }'
```

### 3. Process Customer Email

```bash
curl -X POST "http://localhost:8000/api/v1/email/process" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Need brake pads for 2020 Honda Civic",
    "from_address": "customer@example.com",
    "body": "Hi, I need a set of brake pads for my 2020 Honda Civic. Do you have them in stock at your downtown location?"
  }'
```

### 4. Create Order and Generate Invoice

```bash
# Create order
ORDER_RESPONSE=$(curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Jane Doe",
    "customer_email": "jane@example.com",
    "customer_phone": "555-1234",
    "location_id": "loc-downtown",
    "items": [
      {
        "part_sku": "BRK-PAD-001",
        "part_name": "Ceramic Brake Pads",
        "quantity": 2,
        "unit_price": 89.99
      }
    ],
    "tax_rate": 0.08,
    "notes": "Customer will pick up tomorrow"
  }')

ORDER_ID=$(echo $ORDER_RESPONSE | jq -r '.order_id')

# Generate and send invoice
curl -X POST "http://localhost:8000/api/v1/orders/${ORDER_ID}/invoice"
curl -X POST "http://localhost:8000/api/v1/orders/${ORDER_ID}/invoice/send"
```

### 5. Automated Inbox Processing

```bash
# Process inbox with auto-response enabled
curl -X POST "http://localhost:8000/api/v1/email/process-inbox?limit=20&auto_respond=true"
```

## Background Tasks

The system includes Celery workers that run automatically:

1. **Inbox Processing** (every 5 minutes)
   - Fetches unread emails
   - Classifies intent
   - Generates responses
   - Auto-responds to high-confidence queries
   - Routes low-confidence to human review

2. **Low Stock Monitoring** (daily)
   - Checks inventory levels
   - Generates alerts
   - Emails location managers

3. **Async Operations**
   - Email sending
   - Invoice generation
   - Large batch processing

## Monitoring

### Celery Flower Dashboard

Access at http://localhost:5555

- Task status and history
- Worker health
- Queue monitoring
- Real-time metrics

### Logs

```bash
# API logs
docker-compose logs -f api

# Worker logs
docker-compose logs -f worker

# All services
docker-compose logs -f
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

### Local Development (without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run API server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Run Celery worker (separate terminal)
celery -A backend.workers.celery_app worker --loglevel=info

# Run Celery beat (separate terminal)
celery -A backend.workers.celery_app beat --loglevel=info
```

## Production Deployment

### Cloud Deployment (AWS/GCP)

1. **Container Registry**: Push images to ECR/GCR
2. **Orchestration**: Use ECS/Cloud Run or Kubernetes
3. **Managed Services**:
   - Neo4j AuraDB (graph database)
   - AWS RDS/Cloud SQL (PostgreSQL)
   - ElastiCache/Memorystore (Redis)
   - Qdrant Cloud (vector store)

### Environment Variables

Ensure all production credentials are set:
- Database connection strings
- API keys (Anthropic, Mistral)
- Email credentials
- Neo4j connection

### Scaling Considerations

- **API**: Horizontal scaling via load balancer
- **Workers**: Scale Celery workers based on queue depth
- **Database**: Use read replicas for queries
- **Graph DB**: Neo4j clustering for HA
- **Vector Store**: Qdrant distributed mode

## Troubleshooting

### Neo4j Connection Issues

```bash
# Test Neo4j connection
docker-compose exec api python -c "
from backend.graph.connection import graph_db
import asyncio
asyncio.run(graph_db.connect())
print('Connected successfully')
"
```

### Ollama Not Responding

```bash
# Check Ollama service
ollama list

# Restart Ollama
systemctl restart ollama  # Linux
# or restart the Ollama app on macOS
```

### Email Authentication Errors

For Gmail, create an App Password:
1. Enable 2-factor authentication
2. Go to Security > App Passwords
3. Generate password for "Mail"
4. Use in `.env` file

## Security Notes

- All sensitive data in `.env` (never commit)
- Use app-specific passwords for email
- Implement rate limiting in production
- Enable HTTPS with reverse proxy (nginx/traefik)
- Rotate API keys regularly
- Audit logs for compliance

## Contributing

This is a production system. All changes should:
1. Be tested locally
2. Include error handling
3. Have logging
4. Update documentation
5. Pass linting (black, ruff)

## License

Proprietary - Parts Department System

## Support

For system issues or questions, contact the development team.

