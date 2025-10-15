# Technology Stack - October 2025

**Last Updated**: October 15, 2025

This document outlines the current technology choices and why they're optimal for an auto dealer RAG + Graph system as of October 2025.

## Core Framework

### Python 3.11+
- **Current Version**: 3.11.x / 3.12.x
- **Why**: Best async performance, type hints, pattern matching
- **Status**: Production-ready, widely adopted in 2025

### FastAPI 0.115+
- **Current Version**: 0.115.5
- **Why**: Still the fastest async Python framework in 2025
- **Features**: Auto OpenAPI docs, dependency injection, WebSocket support
- **Status**: Industry standard for microservices

## Database Layer

### Neo4j 5.26+
- **Version**: 5.26.0 (October 2025)
- **Why**: Leading graph database for inventory relationships
- **Deployment**: AuraDB (cloud-native, fully managed)
- **Features**: GQL support, vector indexes (built-in), APOC plugins
- **Status**: Enterprise-grade, billions of nodes capability

### PostgreSQL 16+ with asyncpg
- **Version**: PostgreSQL 16.x, asyncpg 0.30.0
- **Why**: Rock-solid ACID transactions for orders/invoices
- **Features**: Native JSON, advanced indexing, async Python driver
- **Status**: Most advanced open-source RDBMS

## Vector & Embeddings (RAG)

### Qdrant 1.12+
- **Version**: 1.12.1 (October 2025)
- **Why**: Fastest vector search with metadata filtering
- **Features**: HNSW index, payload filtering, horizontal scaling
- **vs Alternatives**: 
  - Faster than Pinecone for multi-tenant scenarios
  - Better filtering than Weaviate
  - More flexible than ChromaDB
- **Status**: Production-ready, used by Fortune 500s

### Sentence Transformers 3.3+
- **Version**: 3.3.1 (October 2025)
- **Models**: 
  - `all-MiniLM-L6-v2` (384 dim, fast)
  - `bge-large-en-v1.5` (1024 dim, accuracy)
  - `gte-large` (1024 dim, latest SOTA)
- **Why**: Best open-source embedding models
- **Status**: Continuously updated, benchmark leaders

## LLM Integration (October 2025)

### Multi-Model Router Strategy

**1. Llama 3.2 (Local via Ollama)**
- **Version**: llama3.2:latest (Oct 2025)
- **Use Case**: Fast, simple queries (80% of traffic)
- **Deployment**: Local via Ollama 0.4.3
- **Cost**: $0 (self-hosted)
- **Performance**: ~50 tokens/sec on M2 Mac

**2. Claude 3.5 Sonnet (Anthropic)**
- **Version**: claude-3-5-sonnet-20241022
- **Use Case**: Complex reasoning, multi-step tasks (15% of traffic)
- **Context**: 200k tokens
- **Cost**: $3/$15 per 1M tokens
- **Why**: Best reasoning model as of Oct 2025

**3. Mistral Large 24.07 (Mistral AI)**
- **Version**: mistral-large-2407
- **Use Case**: Balanced performance/cost (5% of traffic)
- **Context**: 128k tokens
- **Cost**: $2/$6 per 1M tokens
- **Why**: European alternative, GDPR-compliant

### Model Selection Logic (Oct 2025 Best Practice)

```python
if query_complexity == "simple" and latency_critical:
    → Llama 3.2 (local, <100ms)
elif requires_reasoning or query_length > 1000:
    → Claude 3.5 Sonnet (API, best quality)
else:
    → Mistral Large (API, balanced)
```

## Email & Communication

### IMAP/SMTP with aiosmtplib 3.0+
- **Version**: aiosmtplib 3.0.2
- **Why**: Fully async email handling
- **Features**: OAuth2, TLS 1.3, connection pooling
- **Status**: Production-ready

### IMAPClient 3.0+
- **Version**: 3.0.1
- **Why**: Robust IMAP with IDLE support
- **Features**: Auto-reconnect, folder management
- **Status**: Mature, well-maintained

## Background Processing

### Celery 5.4+ with Redis 7+
- **Versions**: Celery 5.4.0, Redis 7.4
- **Why**: Still the gold standard for Python async tasks in 2025
- **Features**: Task priorities, chaining, rate limiting
- **Alternatives Considered**:
  - Dramatiq: Less mature ecosystem
  - RQ: Simpler but less features
  - Temporal: Overkill for our use case

## Document Processing

### WeasyPrint 62+ / ReportLab 4.2+
- **Versions**: WeasyPrint 62.3, ReportLab 4.2.5
- **Why**: Best PDF generation in Python
- **Use Case**: Professional invoices, reports
- **Status**: Production-grade, CSS support

## Containerization & Orchestration

### Docker 24+ / Docker Compose 2.23+
- **Why**: Standard for 2025 deployments
- **Features**: BuildKit, multi-stage builds, health checks
- **Status**: Industry standard

### Kubernetes 1.28+ (Production)
- **Version**: 1.28.x (October 2025)
- **Why**: Auto-scaling, self-healing, rolling updates
- **Deployment**: GKE, EKS, or AKS
- **Status**: Default for enterprise deployments

## Cloud Services (October 2025 Recommendations)

### Graph Database
- **Neo4j AuraDB**: Fully managed, auto-scaling
- **Alternative**: AWS Neptune with openCypher (if AWS-native)

### Vector Database
- **Qdrant Cloud**: Managed clusters, global CDN
- **Alternative**: Self-hosted on Kubernetes

### Relational Database
- **AWS RDS PostgreSQL 16**: Automated backups, read replicas
- **GCP Cloud SQL**: Similar features, better EU presence
- **Alternative**: Supabase (PostgreSQL + real-time)

### Object Storage
- **AWS S3**: Invoice storage, document archives
- **Cloudflare R2**: Zero egress fees (cost optimization)

### Caching & Queue
- **AWS ElastiCache Redis 7**: Managed Redis cluster
- **Upstash Redis**: Serverless Redis (cost-effective)

## Monitoring & Observability (2025 Stack)

### OpenTelemetry
- **Why**: Unified standard for traces, metrics, logs
- **Status**: Industry standard as of 2025
- **Integration**: Native FastAPI support

### Prometheus + Grafana
- **Versions**: Prometheus 2.48+, Grafana 10.2+
- **Why**: De facto standard for metrics
- **Features**: PromQL, alerting, dashboards

### Sentry
- **Why**: Best error tracking for Python
- **Features**: Performance monitoring, session replay
- **Status**: Essential for production

## Security (October 2025 Standards)

### Authentication
- **OAuth 2.1**: Latest OAuth standard
- **JWT with RS256**: Asymmetric tokens
- **Refresh token rotation**: Security best practice

### API Security
- **Rate Limiting**: Redis-based, per-user quotas
- **CORS**: Strict origin validation
- **HTTPS Only**: TLS 1.3 minimum

### Secrets Management
- **AWS Secrets Manager**: Production secrets
- **HashiCorp Vault**: Multi-cloud option
- **Development**: .env files (gitignored)

## Development Tools (October 2025)

### Code Quality
- **Ruff 0.7+**: Ultra-fast linter (replaces flake8, black, isort)
- **mypy**: Static type checking
- **pytest 8.3+**: Testing framework

### AI Code Assistants (2025)
- **GitHub Copilot**: Code completion
- **Cursor**: AI pair programming
- **Aider**: AI git commits

## Why This Stack? (October 2025 Analysis)

### vs. Alternatives

**LangChain/LlamaIndex**: ❌ Removed
- **Why**: Too much abstraction overhead in 2025
- **Our approach**: Direct API calls = simpler, faster, more control

**Supabase vs PostgreSQL**: 
- **Choice**: PostgreSQL (more control)
- **When Supabase**: If need real-time subscriptions

**Pinecone vs Qdrant**:
- **Choice**: Qdrant (better filtering, self-hostable)
- **When Pinecone**: If need managed service + global CDN

**OpenAI vs Claude vs Llama**:
- **Strategy**: Multi-model (cost + quality optimization)
- **Future**: Add GPT-4 if Llama 3.2 insufficient

## Version Update Schedule

| Component | Current | Check Updates | Last Updated |
|-----------|---------|---------------|--------------|
| FastAPI | 0.115.5 | Monthly | Oct 2025 |
| Neo4j | 5.26.0 | Quarterly | Oct 2025 |
| Qdrant | 1.12.1 | Monthly | Oct 2025 |
| Anthropic | 0.40.0 | Monthly | Oct 2025 |
| Python | 3.11+ | Yearly | Oct 2025 |

## Migration Notes

If upgrading from earlier stack:

1. **LangChain removal**: Replace with direct API calls
2. **Qdrant 1.12+**: New filtering API (breaking changes)
3. **FastAPI 0.115+**: Updated dependency injection
4. **Neo4j 5.26**: GQL support (optional upgrade)

## Future-Proofing (2026 Preview)

**Likely additions by Q1 2026**:
- Llama 4 (expected Dec 2025)
- GPT-5 integration (if released)
- Native Neo4j vector indexes (in beta)
- Rust-based embedding models (10x faster)

**Watch List**:
- Milvus 3.0 (alternative vector DB)
- PostgreSQL 17 (SQL/JSON improvements)
- Anthropic Claude 4 (rumored)

## Conclusion

This stack represents best practices as of **October 15, 2025**:
- ✅ Production-tested components
- ✅ Active maintenance and updates
- ✅ Strong community support
- ✅ Cost-optimized for multi-location dealers
- ✅ Scalable to millions of parts/transactions

Last reviewed: October 15, 2025

