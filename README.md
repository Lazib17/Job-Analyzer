# LinkedIn Job Analyzer

AI-powered job matching system that scrapes LinkedIn listings, analyzes them against your CV using Google Gemini, and ranks jobs by compatibility score.

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Backend | Python, FastAPI, Playwright, Google Gemini, Supabase |
| Frontend | React, Tailwind CSS, Axios, React Router, Recharts |
| Database | PostgreSQL (via Supabase) |

## Features

- User authentication (JWT)
- CV upload with PDF/DOCX text extraction
- LinkedIn job scraping with retry & rate-limit handling
- Google Gemini job-resume compatibility analysis
- Ranked job dashboard with compatibility charts
- Missing skills aggregation
- Favorite jobs, re-run analysis, filter by score
- Search history & JSON report export

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- [Supabase](https://supabase.com) account (free tier works)
- [Google AI Studio](https://aistudio.google.com) API key (free tier available)
- (Optional) LinkedIn credentials for authenticated scraping

---

## 1. Database Setup (Supabase)

1. Create a new Supabase project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor** and run the schema from `supabase/schema.sql`
3. Copy your project URL and API keys from **Settings → API**

---

## 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Configure environment
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
```

Edit `backend/.env` with your keys:

```env
SECRET_KEY=your-random-secret-key
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
GOOGLE_API_KEY=AIza...
GOOGLE_MODEL=gemini-2.0-flash
LINKEDIN_EMAIL=optional@email.com
LINKEDIN_PASSWORD=optional-password
```

Start the backend:

```bash
uvicorn main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

---

## 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
```

Start the frontend:

```bash
npm run dev
```

App available at: http://localhost:5173

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login & get JWT token |
| GET | `/auth/me` | Get current user |
| POST | `/upload-resume` | Upload CV (PDF/DOCX) |
| GET | `/resume` | Get latest resume |
| POST | `/search-jobs` | Scrape LinkedIn jobs |
| GET | `/jobs` | List all jobs |
| GET | `/jobs/{id}` | Get job with analysis |
| POST | `/jobs/{id}/favorite` | Toggle favorite |
| POST | `/analyze-job/{id}` | Analyze single job |
| POST | `/analyze-all` | Analyze all unanalyzed jobs |
| POST | `/reanalyze-job/{id}` | Re-run analysis |
| GET | `/ranked-jobs` | Get ranked jobs (with filters) |
| GET | `/skills-gap` | Aggregate missing skills |
| GET | `/export-report` | Export JSON report |
| GET | `/search-history` | View search history |

---

## Usage Workflow

1. **Register / Login** at http://localhost:5173
2. **Upload your CV** (PDF or DOCX) on the Upload page
3. **Search jobs** — enter title, location, and preferences
4. Wait for LinkedIn scraping to complete (1-3 min)
5. Click **Analyze All** on the Results page
6. View **ranked jobs** with compatibility scores on the Dashboard

---

## Project Structure

```
Job Analyzer/
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Environment config
│   ├── database.py             # Supabase client
│   ├── models/                 # Pydantic models
│   ├── routes/                 # API routes
│   ├── services/               # Scraper, Google AI, resume parser
│   └── utils/                  # Auth, ranking
├── frontend/
│   └── src/
│       ├── pages/              # Dashboard, Search, Results, etc.
│       ├── components/         # Navbar, JobCard, ScoreBadge
│       └── api/axios.js        # API client
└── supabase/
    └── schema.sql              # Database schema
```

---

## Notes

- **LinkedIn scraping**: Uses Playwright headless browser. LinkedIn may block requests — add credentials to `.env` for better access. The scraper includes automatic retry and rate-limit backoff.
- **Google AI Studio**: Each job analysis uses one API call. Free tier at [aistudio.google.com](https://aistudio.google.com). Default model: `gemini-2.0-flash` (fast).
- **Resume parsing**: Supports PDF (via pypdf) and DOCX (via python-docx).
- **Security**: Change `SECRET_KEY` in production. Never commit `.env` files.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Playwright browser not found | Run `playwright install chromium` |
| Supabase connection error | Check `SUPABASE_URL` and `SUPABASE_KEY` in `.env` |
| Google AI error | Verify `GOOGLE_API_KEY` at [aistudio.google.com](https://aistudio.google.com) |
| LinkedIn returns 0 jobs | Add LinkedIn credentials or try different search terms |
| CORS errors | Ensure `CORS_ORIGINS` includes your frontend URL |
