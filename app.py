import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from dotenv import load_dotenv
from supabase import create_client, Client
from functools import wraps
import uuid

from stt_service import STTService

load_dotenv()

# --- App and Server Setup ---
app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- Environment and Credentials ---
# Supabase setup
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# --- Flask Routes ---
@app.context_processor
def inject_supabase_keys():
    return dict(supabase_url=supabase_url, supabase_key=supabase_key)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            user_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            session['user'] = {'id': user_response.user.id, 'email': user_response.user.email}
            return redirect(url_for('index'))
        except Exception as e:
            flash(f"Login failed: {e}", "danger")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            res = supabase.auth.sign_up({"email": email, "password": password})
            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Registration failed: {e}", "danger")
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/my-plans')
@login_required
def my_plans():
    return render_template('my_plans.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/transcribe', methods=['POST'])
@login_required
def transcribe_audio():
    if 'audio_file' not in request.files:
        return jsonify({'error': 'No audio file part'}), 400
    
    file = request.files['audio_file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Create a temp directory if it doesn't exist
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Save the file temporarily
    temp_filename = f"{uuid.uuid4()}.mp3"
    temp_filepath = os.path.join(temp_dir, temp_filename)
    file.save(temp_filepath)

    result_text = ''
    try:
        # Get Baidu credentials from environment
        baidu_app_id = os.environ.get("BAIDU_APP_ID")
        baidu_api_key = os.environ.get("BAIDU_API_KEY")
        baidu_secret_key = os.environ.get("BAIDU_SECRET_KEY")

        print(f"[App Debug] BAIDU_APP_ID: {baidu_app_id}")
        print(f"[App Debug] BAIDU_API_KEY: {baidu_api_key}")
        print(f"[App Debug] BAIDU_SECRET_KEY: {baidu_secret_key}")

        if not all([baidu_app_id, baidu_api_key, baidu_secret_key]):
            raise Exception("Baidu voice service not configured on server.")

        # Perform transcription
        stt_service = STTService(baidu_app_id, baidu_api_key, baidu_secret_key, temp_filepath)
        result_text = stt_service.run()

    except Exception as e:
        print(f"Transcription failed: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)

    return jsonify({'text': result_text})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
