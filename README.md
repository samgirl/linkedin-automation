# AI Content Radar

**AI-powered LinkedIn engagement tool** - discover discussions, rank opportunities, and generate thoughtful comments.

Think of this as **Perplexity + Feedly + Linear + Cursor**, but specifically for finding discussions where you should participate.

**This is NOT a LinkedIn automation bot.** It's a discovery and preparation tool.

---

## Quick Start (Local)

```bash
# 1. Clone and setup
cd "linkedin automation"
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your AI provider
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux
# Edit .env with your API key

# 4. Run
streamlit run app.py
```

The app opens at **http://localhost:8501**

---

## Deploy for Everyone

### Option 1: Streamlit Community Cloud (Easiest - Free)

1. Push this repo to GitHub (private repo is fine)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Click "New app" → select your repo, branch `main`, file `app.py`
5. Add secrets in the Streamlit dashboard:
   ```
   AI_PROVIDER = "gemini"
   GEMINI_API_KEY = "your-key-here"
   ```
6. Deploy — everyone gets a URL like `your-app.streamlit.app`

### Option 2: Railway (Recommended - Free Tier)

1. Push to GitHub
2. Go to [railway.app](https://railway.app)
3. Click "New Project" → "Deploy from GitHub"
4. Select your repo
5. Add environment variables in the Railway dashboard:
   ```
   AI_PROVIDER=gemini
   GEMINI_API_KEY=your-key-here
   ```
6. Railway auto-detects the `Procfile` and deploys
7. Get a public URL like `your-app.up.railway.app`

### Option 3: Docker (Self-Hosted)

```bash
# Build
docker compose build

# Run
docker compose up -d

# Access at http://localhost:8501
```

### Option 4: Render (Free Tier)

1. Push to GitHub
2. Go to [render.com](https://render.com)
3. "New" → "Web Service" → connect GitHub repo
4. Build command: `pip install -r requirements.txt`
5. Start command: `streamlit run app.py --server.port $PORT`
6. Add env vars and deploy

### Option 5: Any VPS (DigitalOcean, AWS EC2, etc.)

```bash
# On your server
sudo apt update && sudo apt install python3-pip -y
git clone https://github.com/your-repo/linkedin-automation.git
cd linkedin-automation
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings

# Run with nohup
nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &

# Or use systemd (see below)
```

---

## Features

### Post Creator
- AI writes LinkedIn posts based on your expertise
- Posts directly to LinkedIn via Chrome automation
- Supports photo attachments
- Multiple tone options

### Opportunity Finder
- Searches LinkedIn for relevant discussions
- 7-factor explainable scoring (0-100)
- Factors: keyword match, quality, freshness, engagement, opportunity, novelty, relevance
- Personalized boost from your learning history

### AI Comments
- 5 comment types: Professional, Alternative, Question, Counter-Perspective, Curiosity
- Modular Jinja2 prompt templates (fully customizable)
- Enforces writing guidelines (no flattery, no generic phrases)
- Voice: early-curious professional, not bot

### Keyword Management
- 166+ pre-built keywords across 12 domains
- Add custom keywords with aliases and synonyms
- Domain-based filtering

### Personal Knowledge Base
- Add your projects, interests, technologies
- AI uses this context when generating posts and comments
- Be specific: "Working on precision fermentation scale-up" > "I like biotech"

### Learning System
- Every approve/reject/favorite trains your preferences
- Keyword and domain preference tracking
- Embedding-based similarity matching
- Personalized ranking adjustments over time

### Analytics Dashboard
- Track engagement patterns
- Score distribution charts
- Top keyword and domain stats

### Export
- CSV, JSON, Markdown formats
- Approved comments, all posts, rankings, search history, knowledge base

---

## AI Providers

| Provider | Cost | Setup |
|----------|------|-------|
| **Gemini** | Free tier | Get key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| **OpenAI** | Paid | Get key at [platform.openai.com](https://platform.openai.com) |
| **OpenRouter** | Paid (cheaper) | Get key at [openrouter.ai](https://openrouter.ai) |
| **Ollama** | Free (local) | Install from [ollama.ai](https://ollama.ai), pull `llama3` |

### Environment Variables

```bash
# .env
AI_PROVIDER=gemini              # openai | openrouter | ollama | gemini
GEMINI_API_KEY=your-key-here    # for gemini
GEMINI_MODEL=gemini-2.0-flash
OPENAI_API_KEY=your-key-here    # for openai
OPENAI_MODEL=gpt-4o
OLLAMA_MODEL=llama3             # for ollama

AI_TEMPERATURE=0.7
AI_MAX_TOKENS=500
MAX_COMMENT_WORDS=120
DATABASE_URL=sqlite:///data/content_radar.db
```

---

## Architecture

```
ai_content_radar/
  config/settings.py          # App configuration, .env loading
  models/database.py          # SQLAlchemy ORM (13 tables)
  models/schemas.py           # Pydantic validation schemas
  database/manager.py         # DB sessions, CRUD operations
  services/
    taxonomy.py               # 166+ keyword taxonomy
    search.py                 # Search engine
    ranking.py                # 7-factor explainable ranking
    learning.py               # User preference learning
    embeddings.py             # Embedding generation & similarity
    export.py                 # CSV/JSON/Markdown export
    linkedin.py               # Chrome automation (search, post, comment)
    linkedin_browser.py       # LinkedIn browser search
    linkedin_poster.py        # LinkedIn comment posting
  ai_engine/
    comment_engine.py         # AI comment generation
  ui/
    components.py             # Shared UI components
    pages/
      login_page.py           # User login
      post_page.py            # Post creator
      search_page.py          # Opportunity finder
      keywords_page.py        # Keyword management
      knowledge_page.py       # Personal context
      analytics_page.py       # Analytics dashboard
      history_page.py         # Search history
      settings_page.py        # AI & app settings
  prompts/
    professional_comment.j2   # Professional comment template
    alternative_comment.j2    # Alternative angle template
    question_comment.j2       # Question-based template
    counter_perspective.j2    # Counter-perspective template
    curiosity_comment.j2      # Curiosity-driven template
```

---

## Chrome Integration (Optional)

The LinkedIn features (search, post, comment) require Chrome with remote debugging:

```bash
# Windows
start_chrome.bat

# macOS/Linux
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222
```

1. Chrome opens → log into LinkedIn
2. Keep Chrome open while using the app
3. The app connects via Chrome DevTools Protocol (CDP)

**Note:** The AI post generation and comment writing work without Chrome. Chrome is only needed for posting to LinkedIn.

---

## Testing

```bash
# Run all tests
python -m pytest ai_content_radar/tests/ -v

# Run specific module
python -m pytest ai_content_radar/tests/test_database.py -v
```

---

## Project Philosophy

- **Quality over quantity** — not a spam machine
- **Insight over engagement** — thoughtful, not performative
- **Signal over noise** — minimal, relevant results
- **Professional reputation over content volume** — every comment adds value

### Comment Guidelines

The AI enforces these rules:
- Never summarize posts
- Never use: "Great post", "Interesting", "Thanks for sharing", "Valuable insights"
- Always add perspective, connect ideas, or ask thoughtful questions
- Voice: early-career professional exploring adjacent problems
- Phrases: "We're exploring...", "This overlaps with...", "I'm curious..."

---

## License

MIT
