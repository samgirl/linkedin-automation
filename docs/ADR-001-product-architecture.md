# ADR-001: PROS Product Architecture

**Status**: Accepted
**Date**: 2026-07-18
**Decision Makers**: Founding CTO

---

## Context

We are building an AI Coworker - not a LinkedIn automation tool, not a social media scheduler, not a second brain. It is a quiet, intelligent employee whose only job is making sure the user's work becomes reputation.

The existing codebase (AI Content Radar) is a Python/Streamlit app that searches LinkedIn, ranks posts, and generates comments. It has good foundations (7-factor ranking, learning system, prompt templates) but is fundamentally a single-purpose tool.

We need to rebuild this as a two-engine system:
1. **Context Engine** - Understands everything about the user's professional work
2. **Opportunity Radar** - Scans the outside world and surfaces what matters

---

## Decision

### Architecture: Modular Monolith with Event-Driven Core

**Chosen**: Python monolith with clear module boundaries, Redis for event bus and queues, SQLite for local-first storage, ChromaDB for vectors, Ollama for local LLM inference.

**Rejected Alternatives**:
- **Microservices**: Overkill for initial build. Adds operational complexity without benefit at <100 users.
- **Full TypeScript rewrite**: Loses existing Python investments. Python is fine for this use case.
- **Cloud-first**: Violates zero-cost constraint. Local-first is non-negotiable.

### Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language | Python 3.11+ | Existing codebase, rich AI/ML ecosystem, fast development |
| Backend Framework | FastAPI | Async support, auto-docs, type safety, modern |
| Frontend | React + Vite | More polished than Streamlit, better for daily use |
| Database | SQLite (local) | Zero cost, sufficient for 100K+ memories, portable |
| Vector Store | ChromaDB (local) | Zero cost, good performance, simple API |
| LLM | Ollama (local) | Zero cost, privacy, no API keys needed |
| Cache/Queue | Redis (local) | Fast, reliable, handles events + queues + cache |
| Chrome Extension | Manifest V3 | Standard, works offline, good API |
| Event Bus | Redis Pub/Sub | Zero additional cost, reliable, fast |

### Why Not PostgreSQL?

SQLite with WAL mode handles 100K+ rows easily. It's zero-config, portable (single file), and matches our local-first philosophy. We can migrate to PostgreSQL later if needed.

### Why Not a Separate Queue System?

Redis handles both caching and queuing. Adding RabbitMQ or Kafka adds complexity without benefit at our scale.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER LAYER                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                     │
│  │   Web UI      │  │   Extension  │  │   CLI        │                     │
│  │   (React)     │  │   (Chrome)   │  │   (Future)   │                     │
│  └──────────────┘  └──────────────┘  └──────────────┘                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            API LAYER                                         │
│                    FastAPI (localhost:8000)                                   │
│                    Auth, Rate Limiting, Routing                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  CONTEXT        │         │  OPPORTUNITY    │         │  AI             │
│  ENGINE         │         │  RADAR          │         │  ORCHESTRATOR   │
│                 │         │                 │         │                 │
│ • Events        │         │ • Scanners      │         │ • Ollama        │
│ • Memory        │         │ • Rankers       │         │ • Embeddings    │
│ • Identity      │         │ • Drafters      │         │ • Prompts       │
│ • Reflection    │         │ • Notifiers     │         │                 │
└─────────────────┘         └─────────────────┘         └─────────────────┘
          │                           │                           │
          │                           │                           │
          ▼                           ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DATA LAYER                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  SQLite       │  │  ChromaDB    │  │  Redis       │  │  File System  │  │
│  │  (Primary)    │  │  (Vectors)   │  │  (Cache/Q)   │  │  (Documents)  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BACKGROUND WORKERS                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Event        │  │  Scanner     │  │  Synthesis   │  │  Cleanup     │  │
│  │  Processor    │  │  Workers     │  │  Worker      │  │  Worker      │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Module Design

### Module 1: Context Engine

**Responsibility**: Understand everything about the user's professional work.

**Sub-modules**:
- `events` - Capture and store professional events
- `memory` - Store, decay, and retrieve memories
- `identity` - Build and maintain user model
- `reflection` - Daily conversation to extract insights

**Key Interfaces**:
```python
class ContextEngine:
    async def ingest_event(event: Event) -> Memory
    async def query_context(query: str, limit: int) -> list[Memory]
    async def get_identity() -> Identity
    async def generate_reflection_questions() -> list[Question]
    async def process_reflection(responses: list[Response]) -> list[Memory]
```

### Module 2: Opportunity Radar

**Responsibility**: Scan the outside world and surface what matters.

**Sub-modules**:
- `scanners` - Scan external sources (LinkedIn, GitHub, etc.)
- `rankers` - Score opportunities by relevance
- `drafters` - Generate content suggestions
- `notifiers` - Alert user to time-sensitive opportunities

**Key Interfaces**:
```python
class OpportunityRadar:
    async def scan(sources: list[str]) -> list[Opportunity]
    async def rank(opportunities: list[Opportunity]) -> list[RankedOpportunity]
    async def draft(opportunity: Opportunity) -> Draft
    async def get_daily_briefing() -> Briefing
```

### Module 3: AI Orchestrator

**Responsibility**: Route AI requests to appropriate providers.

**Sub-modules**:
- `providers` - Ollama, OpenAI, etc.
- `embeddings` - Local sentence-transformers
- `prompts` - Template management

**Key Interfaces**:
```python
class AIOrchestrator:
    async def complete(prompt: str, **kwargs) -> str
    async def embed(text: str) -> list[float]
    async def chat(messages: list[Message]) -> str
```

---

## Database Schema

### Core Tables

```sql
-- Events (append-only)
CREATE TABLE events (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL,
    source TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    title TEXT,
    content TEXT,
    metadata JSON,
    embedding_id TEXT,
    processed BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Memories
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    importance REAL DEFAULT 0.5,
    confidence REAL DEFAULT 0.5,
    frequency REAL DEFAULT 0,
    decay_rate REAL DEFAULT 0.01,
    source TEXT,
    embedding_id TEXT,
    tags JSON DEFAULT '[]',
    metadata JSON DEFAULT '{}',
    last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    archived BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Identity nodes
CREATE TABLE identity_nodes (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    data JSON NOT NULL,
    confidence REAL DEFAULT 0.5,
    embedding_id TEXT,
    metadata JSON DEFAULT '{}',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Identity edges (relationships)
CREATE TABLE identity_edges (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    strength REAL DEFAULT 0.5,
    metadata JSON DEFAULT '{}',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, source_id, target_id, relationship_type)
);

-- Saved content (from Chrome extension)
CREATE TABLE saved_content (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    url TEXT NOT NULL,
    title TEXT,
    content TEXT,
    selected_text TEXT,
    website TEXT,
    author TEXT,
    tags JSON DEFAULT '[]',
    notes TEXT,
    embedding_id TEXT,
    metadata JSON DEFAULT '{}',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Opportunities
CREATE TABLE opportunities (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    source TEXT,
    source_url TEXT,
    topics JSON DEFAULT '[]',
    scores JSON NOT NULL,
    recommended_action TEXT,
    reasoning TEXT,
    status TEXT DEFAULT 'pending',
    metadata JSON DEFAULT '{}',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Drafts (generated content)
CREATE TABLE drafts (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL,
    title TEXT,
    content TEXT NOT NULL,
    status TEXT DEFAULT 'draft',
    topics JSON DEFAULT '[]',
    source_memories JSON DEFAULT '[]',
    source_evidence JSON DEFAULT '[]',
    metadata JSON DEFAULT '{}',
    published_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Daily summaries
CREATE TABLE daily_summaries (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    date DATE NOT NULL,
    content TEXT NOT NULL,
    metrics JSON DEFAULT '{}',
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date)
);

-- Connector state
CREATE TABLE connector_state (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    connector_type TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    config JSON DEFAULT '{}',
    last_sync_at DATETIME,
    error_count INTEGER DEFAULT 0,
    metadata JSON DEFAULT '{}',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, connector_type)
);
```

---

## Event System

### Event Types

```python
class EventType(str, Enum):
    # Context events
    MEETING = "meeting"
    RESEARCH = "research"
    ARTICLE_READ = "article_read"
    POST_CREATED = "post_created"
    COMMENT_MADE = "comment_made"
    PROJECT_UPDATE = "project_update"
    LEARNING = "learning"
    IDEA = "idea"
    ACHIEVEMENT = "achievement"
    FRUSTRATION = "frustration"
    
    # Opportunity events
    OPPORTUNITY_FOUND = "opportunity_found"
    OPPORTUNITY_RANKED = "opportunity_ranked"
    DRAFT_GENERATED = "draft_generated"
    
    # System events
    SYNC_COMPLETED = "sync_completed"
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_STRATEGY = "weekly_strategy"
```

### Event Flow

```
External Source → Scanner → Event Created → Event Bus
                                              ↓
                                    ┌─────────────────┐
                                    │  Event Processor │
                                    └─────────────────┘
                                              ↓
                                    ┌─────────────────┐
                                    │  Memory Creator  │
                                    └─────────────────┘
                                              ↓
                                    ┌─────────────────┐
                                    │  Identity Updater│
                                    └─────────────────┘
                                              ↓
                                    ┌─────────────────┐
                                    │  Opportunity     │
                                    │  Evaluator       │
                                    └─────────────────┘
```

---

## AI Orchestration

### Provider Strategy

1. **Default**: Ollama (local, free, private)
2. **Fallback**: OpenAI (if user provides API key)
3. **Embeddings**: sentence-transformers (local, free)

### Model Selection

| Task | Model | Rationale |
|------|-------|-----------|
| General completion | llama3.1:8b | Good balance of quality and speed |
| Embeddings | nomic-embed-text | Fast, local, good quality |
| Quick tasks | phi3 | Lightweight, fast |
| Code understanding | codellama:7b | Specialized for code |

### Prompt Management

All prompts stored as Jinja2 templates in `prompts/` directory. Templates receive context from the relevant module and return structured output.

---

## Chrome Extension Architecture

### Core Features

1. **One-click capture**: Save any page with metadata
2. **Highlight capture**: Save selected text with context
3. **Quick note**: Voice or text note
4. **Contextual memory**: Show related memories when visiting pages
5. **Keyboard shortcuts**: Ctrl+Shift+S to save, Ctrl+Shift+N for note

### Communication

Extension communicates with local API via `http://localhost:8000`. No cloud dependency.

---

## Background Workers

### Worker Types

| Worker | Schedule | Purpose |
|--------|----------|---------|
| Event Processor | Real-time | Process incoming events, create memories |
| Scanner Worker | Every 4 hours | Scan external sources for opportunities |
| Synthesis Worker | Daily 6 AM | Generate daily summary, strategy |
| Decay Worker | Daily 3 AM | Apply memory decay, archive old memories |
| Cleanup Worker | Weekly | Clean cache, optimize database |

### Implementation

Workers run as separate threads within the same process. No separate deployment needed.

---

## Security Model

### Local-First Security

- All data stored locally (SQLite, ChromaDB, Redis)
- No cloud sync by default
- API keys stored in `.env` file
- Extension uses localhost only
- No telemetry, no analytics

### Multi-User (Future)

When needed:
- SQLite per-user databases
- Or PostgreSQL with row-level security
- JWT tokens for API auth

---

## Scalability Plan

### Phase 1: Single User (Current)
- SQLite + ChromaDB + Redis on single machine
- All workers in same process
- Chrome extension connects to localhost

### Phase 2: Small Team (10-50 users)
- PostgreSQL with row-level security
- Separate worker processes
- nginx reverse proxy

### Phase 3: Scale (100+ users)
- PostgreSQL with connection pooling
- Separate worker servers
- Load balancing
- Cloud deployment option

---

## Implementation Order

1. **Foundation**: Project structure, database, config
2. **Context Engine**: Events, memory, identity
3. **AI Orchestrator**: Ollama integration, embeddings
4. **Chrome Extension**: Basic capture functionality
5. **Opportunity Radar**: Scanners, rankers
6. **Background Workers**: Event processing, scanning
7. **API Layer**: REST endpoints
8. **Frontend**: React dashboard
9. **Integration**: Connect all pieces
10. **Polish**: Error handling, logging, tests

---

## Success Criteria

1. User can capture content via Chrome extension in <2 seconds
2. System remembers everything and retrieves relevant context
3. Daily briefing ready before user wakes up
4. Opportunities ranked by genuine relevance, not engagement
5. Content generated from real work, never generic
6. Zero cost to run
7. Works offline for core features

---

## Risks

| Risk | Mitigation |
|------|------------|
| Ollama too slow for real-time | Queue system, async processing |
| SQLite performance at scale | Can migrate to PostgreSQL |
| Chrome extension complexity | Start minimal, iterate |
| LLM quality with small models | Fine-tune prompts, use few-shot |

---

## Notes

This architecture prioritizes:
1. **Simplicity** over cleverness
2. **Local-first** over cloud-first
3. **Working** over perfect
4. **User value** over technical novelty

Every decision should be revisited if it adds complexity without removing meaningful work from the user.
