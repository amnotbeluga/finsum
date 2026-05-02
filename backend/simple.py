from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from datetime import datetime

SUPABASE_URL = "https://nfcsmtqziimepdknstwt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5mY3NtdHF6aWltZXBka25zdHd0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA3MjkyODksImV4cCI6MjA4NjMwNTI4OX0.rcb7CPwCWv0e7Nh-b0MxnsyRA1cuBiNkSBpL7dzWHJs"

app = Flask(__name__)
CORS(app)

print("="*50)
print("🚀 Starting Simple Finserv Backend")
print("="*50)

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase connected!")
    
    test = supabase.table('users').select('*').limit(1).execute()
    print("✅ Database query successful!")
except Exception as e:
    print(f"❌ Supabase connection failed: {e}")
    exit(1)

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({"status": "ok", "message": "Backend is working!"})

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"message": "Email and password required"}), 400
        
        existing = supabase.table('users').select('*').eq('email', email).execute()
        if existing.data:
            return jsonify({"message": "Email already registered"}), 400
        
        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(password)
        
        user_data = {
            'user_id': user_id,
            'email': email,
            'full_name': data.get('fullName', ''),
            'password_hash': password_hash,
            'created_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('users').insert(user_data).execute()
        
        if result.data:
            return jsonify({
                "token": "test-token",
                "user": {
                    "id": user_id,
                    "email": email
                }
            }), 201
        
        return jsonify({"message": "Failed to create user"}), 500
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": str(e)}), 500

@app.route('/api/auth/signin', methods=['POST'])
def signin():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"message": "Email and password required"}), 400
        
        result = supabase.table('users').select('*').eq('email', email).execute()
        
        if not result.data:
            return jsonify({"message": "Invalid email or password"}), 401
        
        user = result.data[0]
        
        if check_password_hash(user['password_hash'], password):
            return jsonify({
                "token": "test-token",
                "user": {
                    "id": user['user_id'],
                    "email": user['email']
                }
            }), 200
        
        return jsonify({"message": "Invalid email or password"}), 401
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": str(e)}), 500

if __name__ == '__main__':
    print("\n📡 Server running at: http://localhost:8000")
    print("🔧 Test endpoint: http://localhost:8000/api/test")
    print("="*50 + "\n")
    app.run(debug=True, port=8000, host='0.0.0.0')