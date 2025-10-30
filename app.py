import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from dotenv import load_dotenv
from supabase import create_client, Client
from functools import wraps
import uuid
from datetime import datetime
from collections import defaultdict

from stt_service import STTService
import models

load_dotenv()

# --- App and Server Setup ---
app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- Environment and Credentials ---
# Supabase setup
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# --- Mock AI Service ---
def generate_plan_mock(query):
    """Mocks a call to an AI service to generate a travel plan."""
    # In a real application, this would call the Gemini API
    # For now, we'll return a hardcoded plan
    
    # Create some itinerary items
    item1 = models.ItineraryItem(
        item_type="Flight",
        description="Flight from New York (JFK) to Tokyo (NRT)",
        start_time=datetime(2025, 11, 10, 9, 0),
        end_time=datetime(2025, 11, 10, 13, 0),
        location=models.Location(name="Tokyo Narita Airport", latitude=35.76, longitude=140.38),
        estimated_cost=2000.0
    )
    item2 = models.ItineraryItem(
        item_type="Hotel",
        description="Check into The Peninsula Tokyo",
        start_time=datetime(2025, 11, 10, 15, 0),
        location=models.Location(name="The Peninsula Tokyo", latitude=35.67, longitude=139.76),
        estimated_cost=500.0
    )
    item3 = models.ItineraryItem(
        item_type="Activity",
        description="Visit the Meiji Shrine",
        start_time=datetime(2025, 11, 11, 10, 0),
        location=models.Location(name="Meiji Shrine", latitude=35.67, longitude=139.69),
        estimated_cost=50.0
    )

    # Group items by day
    day1 = models.Day(date=datetime(2025, 11, 10).date(), items=[item1, item2])
    day2 = models.Day(date=datetime(2025, 11, 11).date(), items=[item3])

    # Create the travel plan
    plan = models.TravelPlan(
        user_id="mock_user", # In a real app, this would be the logged-in user's ID
        title=f"Your Trip to Japan based on: '{query[:20]}...'",
        description="A 5-day trip to explore the wonders of Tokyo.",
        days=[day1, day2]
    )
    return plan

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
            user_data = user_response.user
            session['user'] = {'id': user_data.id, 'email': user_data.email}
            
            # Create or get user from our db
            user = models.get_user(user_data.id)
            if not user:
                user = models.User(id=user_data.id, email=user_data.email)
                models.create_user(user)
            
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
    user_id = session['user']['id']
    plans = models.get_plans_by_user(user_id)
    return render_template('my_plans.html', plans=plans)

@app.route('/plan/<plan_id>')
@login_required
def view_plan(plan_id):
    plan = models.get_plan(plan_id)
    if not plan or plan.user_id != session['user']['id']:
        flash("Plan not found or you don't have access.", "danger")
        return redirect(url_for('my_plans'))

    return render_template('plan_details.html', plan=plan)

@app.route('/generate-plan', methods=['POST'])
@login_required
def generate_plan_route():
    query = request.form.get('query')
    if not query:
        flash("Please provide a query for your travel plan.", "danger")
        return redirect(url_for('index'))

    # Generate the plan (mocked for now)
    plan = generate_plan_mock(query)
    
    # Store plan in session to be able to save it later
    session['generated_plan'] = plan.to_dict()
    
    return render_template('plan_result.html', plan=plan)

@app.route('/save-plan', methods=['POST'])
@login_required
def save_plan_route():
    if 'generated_plan' not in session:
        flash("No plan to save.", "danger")
        return redirect(url_for('index'))

    plan_data = session.pop('generated_plan', None)
    
    days = []
    for day_data in plan_data.get('days', []):
        items = []
        for item_data in day_data.get('items', []):
            location = None
            if item_data.get('location'):
                loc_data = item_data['location']
                location = models.Location(name=loc_data['name'], latitude=loc_data['latitude'], longitude=loc_data['longitude'])
            
            start_time = datetime.fromisoformat(item_data['start_time']) if item_data.get('start_time') else None
            end_time = datetime.fromisoformat(item_data['end_time']) if item_data.get('end_time') else None

            items.append(models.ItineraryItem(
                item_type=item_data['item_type'],
                description=item_data['description'],
                start_time=start_time,
                end_time=end_time,
                location=location,
                estimated_cost=item_data.get('estimated_cost', 0.0),
                actual_cost=item_data.get('actual_cost', 0.0)
            ))
        days.append(models.Day(date=datetime.fromisoformat(day_data['date']).date(), items=items))

    plan = models.TravelPlan(
        user_id=session['user']['id'],
        title=plan_data['title'],
        description=plan_data['description'],
        days=days
    )

    models.create_plan(plan)
    flash("Plan saved successfully!", "success")
    return redirect(url_for('my_plans'))

@app.route('/plan/<plan_id>/delete', methods=['POST'])
@login_required
def delete_plan_route(plan_id):
    plan = models.get_plan(plan_id)
    if not plan or plan.user_id != session['user']['id']:
        flash("Plan not found or you don't have access.", "danger")
        return redirect(url_for('my_plans'))
        
    models.delete_plan(plan_id)
    flash("Plan deleted successfully.", "success")
    return redirect(url_for('my_plans'))

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
