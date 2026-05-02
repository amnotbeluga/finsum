# FinSum Capital 🇮🇳

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-Backend-black.svg?logo=flask)](https://flask.palletsprojects.com/)
[![Supabase](https://img.shields.io/badge/Supabase-Database-green.svg?logo=supabase)](https://supabase.com)
[![Ollama](https://img.shields.io/badge/Ollama-Llama_3-white.svg)](https://ollama.com)

**An Institutional-Grade AI Financial Document Analysis Platform**

FinSum Capital is a comprehensive, full-stack financial intelligence engine engineered for the Indian markets (NSE/BSE). By leveraging advanced NLP, machine learning, and multi-layered data extraction pipelines, it instantly transforms dense annual reports and corporate filings into actionable, quantitative insights.

---

## 🌟 Executive Features

*   **Multi-Engine Document Processing**: Cascading OCR and text extraction (`pdfplumber` → `PyPDF2` → `Camelot` → `Tabula` → `PaddleOCR` → `Tesseract`) combined with OpenCV preprocessing for scanned, low-quality PDFs.
*   **Ensemble Sentiment Analysis**: Weighted fusion of domain-specific models (FinBERT), heuristic engines (VADER, TextBlob), and custom financial lexicon scoring.
*   **BART-Powered Summarization**: Category-aware financial summarization utilizing `facebook/bart-large-cnn`, enhanced with Jaccard deduplication to eliminate redundant insights across sections.
*   **Real-Time Data Aggregation**: Automated retrieval of insider trading data, promoter pledging, and breaking news from Yahoo Finance and Google News RSS.
*   **Conversational AI Assistant**: Native integration with Ollama (Llama 3) for contextual chat regarding the scanned documents, supported by a Gemini 2.0 Flash fallback.
*   **Persistent History & Caching**: All analyses are instantly stored in a Supabase PostgreSQL database using highly optimized `JSONB` caching, allowing for instant reloading without re-processing.
*   **Frictionless Authentication**: Custom JWT infrastructure seamlessly integrated with **Google OAuth Sign-In** for one-click user provisioning.

---

## 🔬 Institutional Risk & Fundamental Scoring

FinSum bridges the gap between qualitative text and quantitative risk by dynamically calculating industry-standard health metrics:

| Metric | Implementation Logic |
|--------|---------------------|
| **Piotroski F-Score** | 9-point fundamental strength assessment measuring profitability, leverage, liquidity, and operating efficiency. |
| **Beneish M-Score** | Probabilistic model utilizing 6 variables (DSRI, GMI, AQI, SGI, TATA, LVGI) to detect earnings manipulation and accounting fraud. |
| **Altman Z-Score** | Bankruptcy probability predictor categorizing firms into Safe, Grey, or Distress zones. |
| **Implied Credit Rating** | A proprietary logic module assigning a synthetic rating (AAA to D) based on aggregated solvency and risk metrics. |
| **Recommendation Engine** | A weighted 0–5 scale logic outputting a specific recommendation (`Strong Buy` → `Sell`) based on Z-Score, F-Score, M-Score, debt, and ROE. |
| **Value at Risk (VaR)** | 95% confidence historical VaR coupled with annualized volatility tracking via 50/200-day SMAs. |

---

## 🛡️ Resilient System Architecture & Failsafes

The system is designed with extreme fault tolerance, ensuring processing never halts due to unexpected document formats or API limits:

| Subsystem | Active Failsafe Mechanism |
|-----------|---------------------------|
| **Symbol Resolution** | If a trading symbol (NSE/BSE) is explicitly missing from the PDF, the engine reverse-lookups the ticker via the **Yahoo Finance Search API** using the extracted company name. |
| **Market Data** | Automatically pivots from `yfinance` to Google Finance web scraping if rate limits are hit. |
| **Table Extraction** | If `Camelot` fails to parse heavily bordered grids, execution seamlessly cascades to `Tabula-py`. |
| **Text Quality Cascade** | If `pdfplumber` extracts < 100 characters (indicating a scanned image), the pipeline triggers OpenCV noise reduction and `PaddleOCR`/`Tesseract`. |
| **LLM Cloud Fallback** | If the local Ollama server is offline, the chat engine dynamically reroutes requests to the Gemini 2.0 Flash Cloud API. |

---

## 🚀 Setup & Deployment

### Prerequisites
*   Python 3.10+
*   [Ollama](https://ollama.com/) (For local LLM processing)
*   *Optional:* Tesseract OCR, Poppler (for `pdf2image`), Java (for `tabula-py`)

### 1. Installation

```bash
git clone https://github.com/amnotbeluga/finsum.git
cd finsum/backend

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file in the `backend/` directory. The application relies on this file to dynamically configure the frontend and backend simultaneously.

```env
# ----------------------------------------
# Supabase Configuration
# ----------------------------------------
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_jwt_key
SECRET_KEY=your_service_role_key
JWT_SECRET=your_jwt_secret

# ----------------------------------------
# Deployment & Hosting Configuration
# ----------------------------------------
PORT=8000
HOST=0.0.0.0
DOMAIN=http://localhost:8000
OLLAMA_API_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3

# ----------------------------------------
# OAuth & AI Providers
# ----------------------------------------
GOOGLE_CLIENT_ID=your_google_cloud_client_id
GEMINI_API_KEY=your_gemini_api_key  # Optional fallback
```

### 3. Database Initialization
Execute the following SQL in your Supabase SQL Editor:

```sql
CREATE TABLE public.users (
    user_id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE public.chat_history (
    id SERIAL PRIMARY KEY,
    user_id TEXT REFERENCES public.users(user_id),
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE public.documents (
    id SERIAL PRIMARY KEY,
    user_id TEXT REFERENCES public.users(user_id),
    filename TEXT,
    company_name TEXT,
    sentiment TEXT,
    analysis_data JSONB,
    uploaded_at TIMESTAMP DEFAULT NOW()
);

-- Note: Row Level Security is disabled for development speed. Enable in production.
ALTER TABLE public.users DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_history DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents DISABLE ROW LEVEL SECURITY;
```

### 4. Boot Sequence

```bash
# Terminal 1: Initialize Local LLM
ollama serve & sleep 2 && ollama pull llama3

# Terminal 2: Initialize FinSum Server
cd backend
python3 app.py
```

Navigate to your `$DOMAIN` (default: `http://localhost:8000`) to access the interface.

---

## 🔌 API Reference

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/signup` | Register a new user |
| `POST` | `/api/auth/signin` | Authenticate and receive a FinSum JWT |
| `POST` | `/api/auth/google` | Verify Google OAuth credentials and auto-provision account |
| `GET`  | `/api/auth/verify` | Validate JWT session token |

### Financial Engine (Protected Routes)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST`   | `/api/analyze` | Execute full pipeline (Extraction → Sentiment → Summary → Risk) |
| `GET`    | `/api/documents` | Retrieve cached document history via `JSONB` payloads |
| `DELETE` | `/api/documents/<id>`| Remove a specific document from history |
| `POST`   | `/api/documents/clear`| Wipe all user document history |
| `POST`   | `/api/chat` | Interact with the active LLM contextually |
| `GET`    | `/api/chat/history` | Retrieve chronological chat logs |

---

<p align="center">
  <i>Engineered for academic and institutional research by <a href="https://github.com/amnotbeluga">amnotbeluga</a></i>
</p>
