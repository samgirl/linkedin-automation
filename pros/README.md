# PROS - Personal Reputation Operating System

**AI Coworker** that quietly works in the background while you focus on building.

This is NOT a LinkedIn automation tool.
This is NOT a social media scheduler.
This is NOT a second brain.

It is an AI coworker whose only job is making sure your work becomes reputation.

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Redis (optional, for caching)
- Ollama (for local AI)

### 1. Install Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Pull models
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

### 2. Start Backend

```bash
cd pros
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
uvicorn pros.src.main:app --reload
```

### 3. Start Frontend

```bash
cd pros/frontend
npm install
npm run dev
```

### 4. Load Chrome Extension

1. Open Chrome, go to `chrome://extensions`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select `pros/extension` folder

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER LAYER                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│  │ Web UI   │  │ Extension│  │ CLI      │                     │
│  │ (React)  │  │ (Chrome) │  │ (Future) │                     │
│  └──────────┘  └──────────┘  └──────────┘                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API LAYER                                   │
│                  FastAPI (localhost:8000)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ CONTEXT ENGINE  │ │ OPPORTUNITY     │ │ AI ORCHESTRATOR │
│                 │ │ RADAR           │ │                 │
│ • Events        │ │ • Scanners      │ │ • Ollama        │
│ • Memory        │ │ • Rankers       │ │ • Embeddings    │
│ • Identity      │ │ • Drafters      │ │ • Prompts       │
│ • Reflection    │ │                 │ │                 │
└─────────────────┘ └─────────────────┘ └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ SQLite   │  │ ChromaDB │  │ Redis    │  │ Files    │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Concepts

### Everything is an Event

Every professional activity becomes an event:
- "Had a meeting"
- "Read this article"
- "Finished a project"
- "Learned something new"

Events update memory → Memory updates identity → Identity generates opportunities.

### Two Engines

1. **Context Engine** - Understands everything about your work
2. **Opportunity Radar** - Scans the world for what matters

### Daily Loop

Every morning, before you open the app, the AI has already:
- Searched
- Filtered
- Ranked
- Connected
- Drafted
- Recommended
- Prepared

---

## API Endpoints

### Events
- `POST /api/v1/events` - Create event
- `GET /api/v1/events` - List events
- `GET /api/v1/events/:id` - Get event

### Memory
- `POST /api/v1/memory` - Create memory
- `GET /api/v1/memory` - List memories
- `POST /api/v1/memory/search` - Search memories

### Identity
- `POST /api/v1/identity/nodes` - Create node
- `GET /api/v1/identity` - Get full identity
- `POST /api/v1/identity/edges` - Create edge

### AI
- `POST /api/v1/ai/complete` - Generate completion
- `POST /api/v1/ai/embed` - Generate embedding

---

## Chrome Extension

One click to capture anything:
- `Ctrl+Shift+S` - Save current page
- `Ctrl+Shift+N` - Quick note
- Right-click → "Save to PROS"

---

## Development

```bash
# Run tests
pytest pros/tests/

# Type checking
mypy pros/src/

# Linting
ruff check pros/src/
```

---

## License

MIT
