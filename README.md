# PROS

Personal Reputation Operating System — an AI-powered anti-doom-scrolling app for entrepreneurs.

## What it does

Instead of spending hours crafting your LinkedIn presence, PROS:

1. **Understands you** — connects to LinkedIn, ChatGPT, Claude, Google to learn how you think, work, and communicate
2. **Builds your context** — gathers everything into a searchable, semantic memory system
3. **Finds opportunities** — scans for posts to comment on, people to connect with, topics to post about
4. **Generates content** — drafts posts, comments, and messages based on YOUR context
5. **Captures daily work** — journal, meeting notes, saved links via web extension

## Quick Start

### With Docker (recommended)

```bash
# 1. Copy env and fill in your keys
cp .env.example .env

# 2. Start everything
docker-compose up

# 3. Open
# Frontend: http://localhost:5173
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Project Structure

```
pros/
├── backend/          # FastAPI API server
│   ├── app/
│   │   ├── api/      # Route handlers
│   │   ├── models/   # Database models
│   │   ├── services/ # Business logic
│   │   └── utils/    # Auth, crypto, helpers
│   └── migrations/   # Database migrations
├── frontend/         # React + Vite + TailwindCSS
│   └── src/
│       ├── pages/    # Dashboard, Context, Opportunities, Journal, etc.
│       ├── components/
│       ├── hooks/
│       └── lib/      # API client
├── extension/        # Chrome extension
└── docker-compose.yml
```

## Features

- **OAuth login** — LinkedIn, Google, Email/Password
- **Context Engine** — ingests events, creates memories, builds identity model
- **Vector search** — semantic search over your context via ChromaDB
- **Opportunity Radar** — AI-powered recommendations for LinkedIn engagement
- **Content Generator** — posts, comments, messages based on your real context
- **Journal** — daily text entries, meeting notes, link drops
- **Chrome Extension** — save any page to your context with one click
- **Dual import** — API key (auto) or JSON export (manual) for ChatGPT/Claude
- **Encrypted credentials** — all OAuth tokens and API keys encrypted at rest
- **Multi-tenant** — isolated data per user with Row-Level Security

## Environment Variables

See `.env.example` for all required configuration.

## License

Private
