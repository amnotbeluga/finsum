#!/bin/bash
echo "Starting environment setup..."

# 1. Activate virtual environment
source venv/bin/activate

# 2. Install all requirements EXCEPT supabase
echo "Installing base requirements..."
grep -v "supabase" requirements.txt > req_no_supa.txt
pip install -r req_no_supa.txt

# 3. Install Supabase's pure-Python dependencies manually
echo "Installing Supabase dependencies..."
pip install httpx yarl typing-extensions websockets deprecation pydantic strenum

# 4. Install Supabase itself forcefully skipping pyiceberg
echo "Installing Supabase (skipping pyiceberg)..."
pip install supabase realtime postgrest storage3 supabase-auth supabase-functions --no-deps

# 5. Patch httpcore for Python 3.14
echo "Patching httpcore for Python 3.14 compatibility..."
sed -i 's/setattr(import_module/try:\n        setattr(import_module/g' venv/lib64/python3.14/site-packages/httpcore/__init__.py
sed -i 's/        import_module.__all__/    except AttributeError:\n        pass\n    import_module.__all__/g' venv/lib64/python3.14/site-packages/httpcore/__init__.py

echo "✅ Environment successfully patched and restored!"
echo "Now run: python3 app.py"
