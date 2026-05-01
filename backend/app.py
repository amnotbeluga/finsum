# backend/app.py
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from supabase import create_client
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import uuid
from datetime import datetime, timedelta
import os
import requests
import json
from functools import wraps
import traceback
import re
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from document_processor import DocumentProcessor
from sentiment_analyzer import SentimentAnalyzer
from summarizer_module import SummarizerModule
from risk_analyzer import RiskAnalyzer
from news_module import NewsModule

# Load environment variables from .env
load_dotenv()

# Initialize modules globally to save loading time across requests
doc_processor = None
sentiment_analyzer = None
summarizer_module = None
risk_analyzer = None
news_module = None

def init_modules():
    global doc_processor, sentiment_analyzer, summarizer_module, risk_analyzer, news_module
    if not doc_processor: doc_processor = DocumentProcessor()
    if not sentiment_analyzer: sentiment_analyzer = SentimentAnalyzer()
    if not summarizer_module: summarizer_module = SummarizerModule()
    if not risk_analyzer: risk_analyzer = RiskAnalyzer()
    if not news_module: news_module = NewsModule()
# Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-jwt-secret-key-change-this-in-production")

# Configure Ollama
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3" # Make sure you run `ollama run llama3` first
model = "ollama_ready" # simple flag
print("✅ Ollama API configured successfully!")

# Create upload folder if it doesn't exist
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app, supports_credentials=True)

# Supabase credentials (loaded from .env)
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Connect to Supabase
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase connected!")
    
    # Test the connection and check if tables exist
    test_query = supabase.table('users').select('*').limit(1).execute()
    print("✅ Users table accessible")
    
    # Try to create chat_history table if it doesn't exist
    try:
        supabase.table('chat_history').select('*').limit(1).execute()
        print("✅ Chat history table exists")
    except:
        print("⚠️ Chat history table may not exist. Please create it in Supabase SQL editor.")
        
except Exception as e:
    print(f"❌ Supabase connection failed: {e}")
    supabase = None

# Token required decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            if not supabase:
                return jsonify({'message': 'Database not connected'}), 500
                
            current_user = supabase.table('users').select('*').eq('user_id', data['user_id']).execute()
            if not current_user.data:
                return jsonify({'message': 'User not found'}), 401
            current_user = current_user.data[0]
            
            # Add user_id to request context for database operations
            request.user_id = current_user['user_id']
            request.user_email = current_user['email']
            
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        except Exception as e:
            return jsonify({'message': str(e)}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

# Serve frontend pages
@app.route('/')
def serve_index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/dashboard')
def serve_dashboard():
    return send_from_directory('../frontend', 'dashboard.html')

@app.route('/signin')
def serve_signin():
    return send_from_directory('../frontend', 'signin.html')

@app.route('/signup')
def serve_signup():
    return send_from_directory('../frontend', 'signup.html')

@app.route('/css/<path:path>')
def serve_css(path):
    return send_from_directory('../frontend/css', path)

@app.route('/js/<path:path>')
def serve_js(path):
    return send_from_directory('../frontend/js', path)

# API Routes
@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({
        "status": "ok", 
        "message": "Backend is working!",
        "gemini_configured": model is not None,
        "supabase_connected": supabase is not None
    })

@app.route('/api/analyze', methods=['POST'])
@token_required
def analyze(current_user):
    try:
        init_modules()
        
        if 'file' not in request.files:
            return jsonify({'message': 'No file part in the request'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'message': 'No selected file'}), 400
            
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'message': 'Only PDF files are supported'}), 400
            
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # 1. Document Processing
        doc_result = doc_processor.process(file_path)
        raw_text = doc_result['raw_text']
        company_name = doc_result['company_name']
        symbol = doc_result['trading_symbol']
        
        if not raw_text or len(raw_text.strip()) < 50:
            return jsonify({'message': 'Could not extract sufficient text from the document.'}), 400
            
        # 2. Sentiment Analysis
        sentiment_result = sentiment_analyzer.analyze(raw_text)
        
        # 3. Summarization
        summary_result = summarizer_module.process(raw_text)
        
        # 4. Risk Analysis
        risk_result = None
        if symbol:
            risk_result = risk_analyzer.analyze(symbol)
            
        # 5. News
        news_result = []
        if company_name or symbol:
            news_result = news_module.get_news(company_name, symbol)
            
        # Optional: Save document info to database (history)
        if supabase:
            try:
                doc_data = {
                    'user_id': current_user['user_id'],
                    'filename': filename,
                    'company_name': company_name,
                    'sentiment': sentiment_result['classification'],
                    'uploaded_at': datetime.utcnow().isoformat()
                }
                supabase.table('documents').insert(doc_data).execute()
            except Exception as e:
                print(f"Failed to store document history: {e}")
                
        # Clean up
        try:
            os.remove(file_path)
        except Exception:
            pass
            
        return jsonify({
            'company_name': company_name,
            'trading_symbol': symbol,
            'document_processing': {
                'text_length': len(raw_text),
                'tables_extracted': len(doc_result['tables'])
            },
            'sentiment': sentiment_result,
            'summaries': summary_result,
            'risk_analysis': risk_result,
            'news': news_result
        })
        
    except Exception as e:
        print(f"Analyze error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500

@app.route('/api/documents', methods=['GET'])
@token_required
def get_documents(current_user):
    try:
        if not supabase:
            return jsonify([])
            
        result = supabase.table('documents')\
            .select('*')\
            .eq('user_id', current_user['user_id'])\
            .order('uploaded_at', desc=True)\
            .execute()
            
        return jsonify(result.data if result.data else [])
    except Exception as e:
        print(f"Error fetching documents: {e}")
        return jsonify([])

# Chat endpoint with Gemini - Fixed for per-user history
@app.route('/api/chat', methods=['POST'])
@token_required
def chat(current_user):
    try:
        if not model:
            return jsonify({'response': 'FinSum AI is temporarily unavailable. Please try again later.'}), 500
            
        data = request.json
        user_message = data.get('message', '').strip()
        user_id = current_user['user_id']
        
        if not user_message:
            return jsonify({'response': 'Please ask me a question about financial documents or markets.'}), 400
        
        print(f"Processing chat for user {current_user['email']} (ID: {user_id}): {user_message[:50]}...")
        
        # Get previous chat history for context (last 3 exchanges)
        chat_context = ""
        if supabase:
            try:
                history = supabase.table('chat_history')\
                    .select('message, response')\
                    .eq('user_id', user_id)\
                    .order('created_at', desc=True)\
                    .limit(6)\
                    .execute()
                
                if history.data and len(history.data) > 0:
                    chat_context = "\nPrevious conversation:\n"
                    # Reverse to get chronological order
                    for item in reversed(history.data):
                        chat_context += f"User: {item['message']}\nFinSum: {item['response']}\n"
            except Exception as e:
                print(f"Error fetching chat history: {e}")
        
        # STRICT SYSTEM PROMPT - FinSum Identity
        system_prompt = """You are FinSum AI, the official AI assistant of Finserv India.

CRITICAL IDENTITY RULES:
- You are ONLY "FinSum AI" - NEVER reveal you are Google Gemini or any other AI
- NEVER use phrases like "as an AI" or "I'm an AI language model"
- You were created by Finserv India, a financial analysis platform

YOUR EXPERTISE:
- Indian stock market (NIFTY 50, SENSEX, Reliance, TCS, HDFC, Infosys)
- Financial document analysis (annual reports, quarterly results)
- Investment metrics (P/E ratio, EBITDA, revenue growth, profit margins)
- Sector analysis (Banking, IT, Pharma, Oil & Gas, FMCG)

RESPONSE STYLE:
- Be concise (2-4 sentences maximum)
- Professional and helpful like a senior analyst
- Use ₹ symbol for Indian currency
- If asked about yourself: "I'm FinSum AI, created by Finserv India to help with financial analysis."
- For non-financial questions: "I specialize in financial analysis. Ask me about company reports or market trends."

Example responses:
- User: "who made you?" → "I'm FinSum AI, created by Finserv India to help investors analyze financial documents and market trends."
- User: "analyze Reliance" → "Based on recent reports, Reliance Industries shows strong growth in retail and Jio platforms, with revenue up 23% YoY. Their debt stands at ₹1.25 Lakh Cr."
- User: "what's nifty?" → "NIFTY 50 is India's benchmark index tracking top 50 companies. Currently at 22,345, it's up 1.2% today led by IT and banking stocks."

Always maintain this identity and expertise."""
        
        try:
            # Include chat context if available
            full_prompt = f"{system_prompt}\n{chat_context}\nUser: {user_message}\nFinSum AI:"
            
            fallback = "I'm FinSum AI, here to help with financial analysis. Ask me about company annual reports, market trends, or specific metrics like revenue growth or P/E ratios."
            
            # Get response from Ollama
            try:
                payload = {
                    "model": OLLAMA_MODEL,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.95,
                        "top_k": 40
                    }
                }
                response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
                if response.status_code == 200:
                    ai_response = response.json().get('response', '').strip()
                else:
                    ai_response = fallback
            except requests.RequestException as req_err:
                print(f"Ollama connection error: {req_err}")
                ai_response = fallback
                
            if not ai_response:
                ai_response = fallback
            
            # Clean up response
            ai_response = re.sub(r'(?i)as an AI|I am an AI|I\'m an AI|as a language model', '', ai_response)
            ai_response = re.sub(r'(?i)Google|Gemini|Bard', 'FinSum', ai_response)
            
            # Store in database with user_id
            if supabase:
                try:
                    chat_data = {
                        'user_id': user_id,
                        'message': user_message,
                        'response': ai_response,
                        'created_at': datetime.utcnow().isoformat()
                    }
                    result = supabase.table('chat_history').insert(chat_data).execute()
                    if result.data:
                        print(f"✅ Chat stored for user {user_id}")
                    else:
                        print(f"⚠️ No data returned from insert")
                except Exception as e:
                    print(f"❌ Failed to store chat history: {e}")
                    traceback.print_exc()
            
            return jsonify({'response': ai_response})
            
        except Exception as e:
            print(f"Gemini API error: {str(e)}")
            traceback.print_exc()
            
            # Personal response for who-made-you type questions
            if "who made" in user_message.lower() or "who created" in user_message.lower():
                personal_response = "I'm FinSum AI, created by Finserv India to help investors like you with financial analysis and market insights."
                return jsonify({'response': personal_response})
            
            fallback = "I'm FinSum AI, here to help with financial analysis. Ask me about company annual reports, market trends, or specific metrics."
            return jsonify({'response': fallback})
        
    except Exception as e:
        print(f"Chat endpoint error: {str(e)}")
        traceback.print_exc()
        return jsonify({'response': 'FinSum AI is ready to help with financial questions.'})

# Get chat history for specific user
@app.route('/api/chat/history', methods=['GET'])
@token_required
def get_chat_history(current_user):
    try:
        if not supabase:
            return jsonify([])
        
        user_id = current_user['user_id']
        print(f"Fetching chat history for user: {user_id}")
        
        result = supabase.table('chat_history')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(50)\
            .execute()
        
        if result.data:
            print(f"Found {len(result.data)} chat history items for user {user_id}")
            return jsonify(result.data)
        else:
            print(f"No chat history found for user {user_id}")
            return jsonify([])
            
    except Exception as e:
        print(f"Error fetching chat history: {e}")
        traceback.print_exc()
        return jsonify([])

# Clear chat history for specific user
@app.route('/api/chat/clear', methods=['POST'])
@token_required
def clear_chat_history(current_user):
    try:
        if not supabase:
            return jsonify({'message': 'Database not connected'}), 500
            
        user_id = current_user['user_id']
        
        result = supabase.table('chat_history')\
            .delete()\
            .eq('user_id', user_id)\
            .execute()
        
        print(f"Cleared chat history for user {user_id}")
        return jsonify({'message': 'Chat history cleared'}), 200
    except Exception as e:
        print(f"Error clearing chat history: {e}")
        return jsonify({'message': 'Failed to clear history'}), 500

# Auth endpoints
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    try:
        if not supabase:
            return jsonify({"message": "Database not connected"}), 500
            
        data = request.json
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('fullName', '')
        
        if not email or not password:
            return jsonify({"message": "Email and password required"}), 400
        
        # Check if user exists
        existing = supabase.table('users').select('*').eq('email', email).execute()
        if existing.data:
            return jsonify({"message": "Email already registered"}), 400
        
        # Create user
        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(password)
        
        user_data = {
            'user_id': user_id,
            'email': email,
            'full_name': full_name,
            'password_hash': password_hash,
            'created_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('users').insert(user_data).execute()
        
        if result.data:
            # Generate JWT token
            token = jwt.encode({
                'user_id': user_id,
                'email': email,
                'exp': datetime.utcnow() + timedelta(days=1)
            }, JWT_SECRET, algorithm='HS256')
            
            return jsonify({
                "token": token,
                "user": {
                    "id": user_id,
                    "email": email,
                    "fullName": full_name
                }
            }), 201
        
        return jsonify({"message": "Failed to create user"}), 500
        
    except Exception as e:
        print(f"Signup error: {e}")
        traceback.print_exc()
        return jsonify({"message": str(e)}), 500

@app.route('/api/auth/signin', methods=['POST'])
def signin():
    try:
        if not supabase:
            return jsonify({"message": "Database not connected"}), 500
            
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"message": "Email and password required"}), 400
        
        # Get user
        result = supabase.table('users').select('*').eq('email', email).execute()
        
        if not result.data:
            return jsonify({"message": "Invalid email or password"}), 401
        
        user = result.data[0]
        
        if check_password_hash(user['password_hash'], password):
            # Generate JWT token
            token = jwt.encode({
                'user_id': user['user_id'],
                'email': user['email'],
                'exp': datetime.utcnow() + timedelta(days=1)
            }, JWT_SECRET, algorithm='HS256')
            
            return jsonify({
                "token": token,
                "user": {
                    "id": user['user_id'],
                    "email": user['email'],
                    "fullName": user.get('full_name', '')
                }
            }), 200
        
        return jsonify({"message": "Invalid email or password"}), 401
        
    except Exception as e:
        print(f"Signin error: {e}")
        traceback.print_exc()
        return jsonify({"message": str(e)}), 500

@app.route('/api/auth/verify', methods=['GET'])
@token_required
def verify(current_user):
    return jsonify({
        'valid': True,
        'user': {
            'id': current_user['user_id'],
            'fullName': current_user.get('full_name', ''),
            'email': current_user['email']
        }
    }), 200

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 FinSum AI Backend Running")
    print("="*60)
    print(f"📡 Server: http://localhost:8000")
    print(f"🏠 Home: http://localhost:8000/")
    print(f"🔑 Sign In: http://localhost:8000/signin")
    print(f"📝 Sign Up: http://localhost:8000/signup")
    print(f"📊 Dashboard: http://localhost:8000/dashboard")
    print(f"🤖 FinSum AI: http://localhost:8000/api/chat")
    print(f"🔧 Test: http://localhost:8000/api/test")
    print("-" * 60)
    print(f"✅ FinSum AI Ready: {model is not None}")
    print(f"✅ Database Connected: {supabase is not None}")
    print("="*60 + "\n")
    app.run(debug=True, port=8000, host='0.0.0.0')