# FinSum Capital India 🇮🇳

**AI-Powered Financial Document Analysis Platform for Indian Markets**

FinSum Capital is a full-stack financial intelligence platform that analyzes company annual reports, quarterly filings, and financial documents using NLP and machine learning. Upload a PDF — get sentiment analysis, risk metrics, AI-generated summaries, and live market news in seconds.

---

## ✨ Features

| Module | Description |
|--------|-------------|
| 📄 **Document Processing** | Extract text and tables from PDFs using pdfplumber, Camelot, Tabula, and PaddleOCR (supports scanned documents) |
| 🧠 **Sentiment Analysis** | Multi-model ensemble — FinBERT, VADER, TextBlob, and keyword-based scoring with weighted fusion |
| 📝 **Summarization** | Category-aware summarization using BART (`facebook/bart-large-cnn`) with sentence scoring |
| ⚠️ **Risk Analysis** | Altman Z-Score, VaR (95%), annualized volatility, moving averages, and auto-generated buy/sell recommendations via yfinance |
| 📰 **News Aggregation** | Real-time financial news from Google News RSS and Yahoo Finance with sentiment tagging |
| 🤖 **AI Chat Assistant** | Chat with FinSum AI powered by Ollama (Llama 3) for financial Q&A |
| 🔐 **Auth System** | JWT-based authentication with Supabase (PostgreSQL) backend |

---

## 🏗️ Architecture

```
finsum/
├── backend/
│   ├── app.py                  # Flask API server (main entry point)
│   ├── document_processor.py   # PDF text/table extraction + OCR
│   ├── sentiment_analyzer.py   # FinBERT + VADER + TextBlob ensemble
│   ├── summarizer_module.py    # BART-based category-aware summarizer
│   ├── risk_analyzer.py        # Altman Z-Score, VaR, volatility
│   ├── news_module.py          # Google News + yfinance news aggregator
│   ├── requirements.txt        # Python dependencies
│   ├── setup_env.sh            # Automated environment setup script
│   └── .env                    # Environment variables (not tracked)
├── frontend/
│   ├── index.html              # Landing page
│   ├── signin.html             # Sign in page
│   ├── signup.html             # Sign up page
│   ├── dashboard.html          # Main dashboard (post-login)
│   ├── css/style.css           # Stylesheet
│   └── js/
│       ├── auth.js             # Authentication logic
│       └── dashboard.js        # Dashboard interactions
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
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_jwt_key
SECRET_KEY=your_service_role_key
JWT_SECRET=your_jwt_secret
```

> **Where to find these:** Supabase Dashboard → Project Settings → API
> - `SUPABASE_URL` → Project URL
> - `SUPABASE_KEY` → `anon` `public` key (starts with `eyJ...`)
> - `SECRET_KEY` → `service_role` `secret` key
> - `JWT_SECRET` → JWT Settings → Legacy JWT Secret

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

-- Documents table
CREATE TABLE public.documents (
    id SERIAL PRIMARY KEY,
    user_id TEXT REFERENCES public.users(user_id),
    filename TEXT,
    company_name TEXT,
    sentiment TEXT,
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

> **Note:** Tesseract is optional — the app works without it for text-based PDFs.

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
| `POST` | `/api/auth/signin` | Sign in and receive JWT |
| `GET` | `/api/auth/verify` | Verify JWT token |

### Core Features (requires JWT)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Upload PDF for full analysis (sentiment + summary + risk + news) |
| `GET` | `/api/documents` | Get user's document analysis history |
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
| **Backend** | Python, Flask, Flask-CORS |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Database** | Supabase (PostgreSQL) |
| **AI/ML** | FinBERT, BART, VADER, TextBlob, NLTK |
| **LLM** | Ollama + Llama 3 |
| **PDF Processing** | pdfplumber, PyPDF2, Camelot, Tabula, PaddleOCR, Tesseract |
| **Finance Data** | yfinance, Google News RSS |
| **Auth** | JWT (PyJWT), Werkzeug password hashing |

---

## 📄 License

This project is for educational and research purposes.

---

<p align="center">
  Built with ❤️ by <a href="https://github.com/amnotbeluga">amnotbeluga</a>
</p>
