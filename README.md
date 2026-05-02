# FinSum Capital India 🇮🇳

**AI-Powered Financial Document Analysis Platform for Indian Markets**

FinSum Capital is a full-stack financial intelligence platform that analyzes company annual reports, quarterly filings, and financial documents using NLP and machine learning. Upload a PDF — get sentiment analysis, risk metrics, AI-generated summaries, and live market news in seconds.

---

## ✨ Features

| Module | Description |
|--------|-------------|
| 📄 **Document Processing** | Multi-engine cascading extraction (pdfplumber → PyPDF2 → Camelot → Tabula → PaddleOCR → Tesseract) with OpenCV image preprocessing for scanned documents |
| 🧠 **Sentiment Analysis** | Multi-model ensemble — FinBERT, VADER, TextBlob, and keyword-based scoring with weighted fusion. Local model caching for 5s startup |
| 📝 **Summarization** | Category-aware summarization using BART (`facebook/bart-large-cnn`) with Jaccard deduplication (85% threshold) and 4-worker parallel processing |
| ⚠️ **Risk Analysis** | Altman Z-Score, Piotroski F-Score (9-point), Beneish M-Score (earnings manipulation), VaR (95%), annualized volatility, and Implied Credit Rating (AAA-D) |
| 📊 **Investment Engine** | 0–5 scale recommendation engine (Strong Buy → Sell) using weighted scoring of Z-Score, F-Score, M-Score, debt, and ROE |
| 📈 **Technical Analysis** | 5-year historical SMA (50-day & 200-day moving averages) for trend identification |
| 🏛️ **Insider Data** | Promoter holding, promoter pledging percentage, and insider trading activity from NSE/yfinance |
| 📰 **News Aggregation** | Real-time financial news from Google News RSS and Yahoo Finance with sentiment tagging |
| 🤖 **AI Chat Assistant** | Chat with FinSum AI powered by Ollama (Llama 3) with Gemini API fallback |
| 🔐 **Auth System** | JWT-based auth + **Google OAuth Sign-In** natively integrated with Supabase (PostgreSQL) backend |
| 📋 **Scan History** | Persistent document analysis history stored in Supabase with full JSON cache for instant "View Analysis" reloads |

---

## 🔬 Institutional-Grade Analysis

### Scoring Systems

| Metric | Implementation |
|--------|---------------|
| **Piotroski F-Score** | 9-point fundamental strength assessment (ROA, cash flow, leverage, margins, asset turnover) |
| **Beneish M-Score** | Probabilistic earnings manipulation detection (DSRI, GMI, AQI, SGI, TATA, LVGI) |
| **Altman Z-Score** | Bankruptcy probability predictor (Safe/Grey/Distress zones) |
| **Implied Credit Rating** | Composite rating from AAA to D based on aggregated risk metrics |
| **Investment Recommendation** | Weighted 0-5 scale: Strong Buy, Buy, Accumulate on Dips, Hold, Reduce, Sell |

### System Failsafes

| Failsafe | Fallback |
|----------|----------|
| **Yahoo Finance API** | Automatically pivots to Google Finance web scraping if rate-limited |
| **Ollama LLM** | Falls back to Gemini 2.0 Flash cloud API if local server is down |
| **PaddleOCR** | Falls back to Tesseract → pdfplumber force-extraction |
| **Camelot Tables** | Falls back to Tabula-py for table extraction |
| **PDF Text Quality** | Quality check cascade — if pdfplumber extracts <100 chars, falls back to PyPDF2 |

### Performance Optimizations

| Optimization | Improvement |
|-------------|-------------|
| **Model Caching** | Local `.model_cache/` directory — reduces FinBERT/BART startup from ~50s to ~5s |
| **Parallel Processing** | `ThreadPoolExecutor` with 4 workers for sentiment + summary + risk + news |
| **Jaccard Deduplication** | 85% similarity threshold prevents duplicate summaries across categories |
| **OpenCV Preprocessing** | Grayscale, adaptive thresholding, median blur for 72 DPI scanned PDFs |

---

## 🏗️ Architecture

```
finsum/
├── backend/
│   ├── app.py                  # Flask API server with parallel processing & LLM fallback
│   ├── document_processor.py   # Cascading PDF extraction + OpenCV preprocessing
│   ├── sentiment_analyzer.py   # FinBERT + VADER + TextBlob ensemble with model caching
│   ├── summarizer_module.py    # BART summarizer with Jaccard dedup + ThreadPoolExecutor
│   ├── risk_analyzer.py        # F-Score, M-Score, Z-Score, Credit Rating, insider data
│   ├── news_module.py          # Google News + yfinance news aggregator
│   ├── requirements.txt        # Python dependencies
│   ├── setup_env.sh            # Automated environment setup script
│   └── .env                    # Environment variables (not tracked)
├── frontend/
│   ├── index.html              # Landing page
│   ├── signin.html             # Sign in page
│   ├── signup.html             # Sign up page
│   ├── dashboard.html          # Dashboard with scan history + analysis results
│   ├── css/style.css           # Stylesheet
│   └── js/
│       ├── auth.js             # Authentication logic
│       └── dashboard.js        # Dashboard interactions + document history
├── agents/
│   ├── summarizer.py           # Standalone financial document summarizer
│   ├── multimodel.py           # Multi-model comparison tool (BART, PEGASUS, T5, DistilBART)
│   └── summaries/              # Pre-generated summary outputs
├── .gitignore
└── README.md
```

---

## 🚀 Setup & Installation

### Prerequisites

- **Python 3.10+**
- **Ollama** (for AI chat) — [ollama.com](https://ollama.com)
- **Tesseract OCR** (optional, for scanned PDFs)
- **Poppler** (for `pdf2image`)
- **Java** (for `tabula-py`)

### 1. Clone the Repository

```bash
git clone https://github.com/amnotbeluga/finsum.git
cd finsum
```

### 2. Set Up the Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Option A: Use the setup script (handles Supabase + Python 3.14 patches)
bash setup_env.sh

# Option B: Install manually
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_jwt_key
SECRET_KEY=your_service_role_key
JWT_SECRET=your_jwt_secret

# Deployment & Hosting Configuration
PORT=8000
HOST=0.0.0.0
DOMAIN=http://localhost:8000
OLLAMA_API_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3

# Google OAuth
GOOGLE_CLIENT_ID=your_google_cloud_client_id

# Optional LLM Fallback
GEMINI_API_KEY=your_gemini_api_key
```

> **Where to find these:** Supabase Dashboard → Project Settings → API
> - `SUPABASE_URL` → Project URL
> - `SUPABASE_KEY` → `anon` `public` key (starts with `eyJ...`)
> - `SECRET_KEY` → `service_role` `secret` key
> - `JWT_SECRET` → JWT Settings → Legacy JWT Secret
> - `GEMINI_API_KEY` → [Google AI Studio](https://aistudio.google.com/apikey) (optional fallback)

### 4. Set Up Supabase Tables

Create the following tables in your [Supabase](https://supabase.com) SQL editor:

```sql
-- Users table
CREATE TABLE public.users (
    user_id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Chat history table
CREATE TABLE public.chat_history (
    id SERIAL PRIMARY KEY,
    user_id TEXT REFERENCES public.users(user_id),
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Documents table (scan history)
CREATE TABLE public.documents (
    id SERIAL PRIMARY KEY,
    user_id TEXT REFERENCES public.users(user_id),
    filename TEXT,
    company_name TEXT,
    sentiment TEXT,
    analysis_data JSONB,
    uploaded_at TIMESTAMP DEFAULT NOW()
);

-- Disable RLS (app handles auth via Flask + JWT)
ALTER TABLE public.users DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_history DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents DISABLE ROW LEVEL SECURITY;
```

### 5. Install & Run Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start the server and pull the model
ollama serve > /dev/null 2>&1 & sleep 2 && ollama pull llama3
```

### 6. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt install tesseract-ocr poppler-utils default-jre
```

**Fedora/Bazzite (immutable):**
```bash
rpm-ostree install tesseract poppler-utils java-17-openjdk
systemctl reboot
```

**macOS:**
```bash
brew install tesseract poppler java
```

> **Note:** Tesseract and OpenCV are optional — the app works without them for text-based PDFs.

---

## ▶️ Running the Application

```bash
# Terminal 1: Start Ollama (if not already running)
ollama serve > /dev/null 2>&1 &

# Terminal 2: Start the backend
cd backend
source venv/bin/activate
python3 app.py
```

Open your browser and navigate to:

| Page | URL |
|------|-----|
| 🏠 Landing Page | http://localhost:8000/ |
| 🔑 Sign In | http://localhost:8000/signin |
| 📝 Sign Up | http://localhost:8000/signup |
| 📊 Dashboard | http://localhost:8000/dashboard |
| 🔧 Health Check | http://localhost:8000/api/test |

---

## 🔌 API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/signup` | Register a new user |
| `POST` | `/api/auth/signin` | Sign in and receive custom JWT |
| `POST` | `/api/auth/google` | Google OAuth token verification & auto-provisioning |
| `GET`  | `/api/auth/verify` | Verify custom JWT token |

### Core Features (requires JWT)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Upload PDF for full analysis (sentiment + summary + risk + news) |
| `GET` | `/api/documents` | Get user's document scan history |
| `POST` | `/api/chat` | Chat with FinSum AI |
| `GET` | `/api/chat/history` | Get user's chat history |
| `POST` | `/api/chat/clear` | Clear user's chat history |

### Example: Analyze a Document

```bash
# Sign in first
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/signin \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpassword"}' | jq -r '.token')

# Upload and analyze a PDF
curl -X POST http://localhost:8000/api/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@annual_report.pdf"
```

### Analysis Response Schema

```json
{
  "company_name": "Reliance Industries Limited",
  "trading_symbol": "RELIANCE",
  "document_processing": {
    "text_length": 45230,
    "tables_extracted": 12,
    "extraction_method": "pdfplumber",
    "is_scanned": false
  },
  "sentiment": {
    "score": 0.4523,
    "classification": "Positive",
    "components": { "keyword": 0.65, "finbert": 0.42, "vader": 0.35, "textblob": 0.28 }
  },
  "risk_analysis": {
    "altman_z_score": 3.24,
    "piotroski_f_score": 7,
    "beneish_m_score": -2.85,
    "credit_rating": "AA",
    "recommendation": "Buy",
    "insider_data": { "promoter_holding": 50.6, "promoter_pledging": "0.00" }
  }
}
```

---

## 🧪 Standalone Agents

The `agents/` directory contains standalone summarization tools that can be run independently:

```bash
cd agents
pip install -r requirements.txt

# Multi-model comparison (BART, PEGASUS, T5, DistilBART)
python3 multimodel.py
```

This will prompt you to select a PDF and compare summaries across 4 different transformer models.

---

## 🛠️ Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python, Flask, Flask-CORS, ThreadPoolExecutor |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Database** | Supabase (PostgreSQL) |
| **AI/ML** | FinBERT, BART, VADER, TextBlob, NLTK |
| **LLM** | Ollama + Llama 3 (primary), Google Gemini 2.0 Flash (fallback) |
| **PDF Processing** | pdfplumber, PyPDF2, Camelot, Tabula, PaddleOCR, Tesseract, OpenCV |
| **Finance Data** | yfinance, Google Finance (fallback), Google News RSS |
| **Risk Models** | Altman Z-Score, Piotroski F-Score, Beneish M-Score |
| **Auth** | JWT (PyJWT), Werkzeug password hashing |

---

## 📄 License

This project is for educational and research purposes.

---

<p align="center">
  Built with ❤️ by <a href="https://github.com/amnotbeluga">amnotbeluga</a>
</p>
