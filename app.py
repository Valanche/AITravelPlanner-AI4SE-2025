import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from dotenv import load_dotenv
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from dotenv import load_dotenv
from functools import wraps
import uuid
from datetime import datetime

from stt_service import STTService
import models
import llm_service

load_dotenv()

# --- App and Server Setup ---
app = Flask(__name__)
app.secret_key = os.urandom(24)

def _create_plan_object_from_dict(plan_data: dict) -> models.TravelPlan:
    """Converts a dictionary (from LLM) to a TravelPlan object."""
    days = []
    location_map = {}
    for day_data in plan_data.get('days', []):
        items = []
        for item_data in day_data.get('items', []):
            location = None
            if item_data.get('location'):
                loc_data = item_data['location']
                # Use a tuple of (name, city) as a key to uniquely identify locations
                loc_key = (loc_data.get('name'), loc_data.get('city'))
                if loc_key in location_map:
                    location = location_map[loc_key]
                else:
                    location = models.Location(name=loc_data.get('name'), city=loc_data.get('city'))
                    location_map[loc_key] = location
            
            start_time = datetime.fromisoformat(item_data['start_time']) if item_data.get('start_time') else None
            end_time = datetime.fromisoformat(item_data['end_time']) if item_data.get('end_time') else None

            items.append(models.ItineraryItem(
                item_type=item_data.get('item_type'),
                description=item_data.get('description'),
                start_time=start_time,
                end_time=end_time,
                location=location,
                estimated_cost=item_data.get('estimated_cost', 0.0),
                estimated_cost_currency=item_data.get('estimated_cost_currency', 'USD'),
                actual_costs=[] # Actual costs are added by the user later
            ))
        days.append(models.Day(date=datetime.fromisoformat(day_data['date']).date(), items=items))

    plan = models.TravelPlan(
        user_id=session.get('user', {}).get('id'), # Get user_id from session
        title=plan_data.get('title'),
        description=plan_data.get('description'),
        days=days
    )
    return plan

# --- Flask Routes ---
@app.context_processor
def inject_supabase_keys():
    return dict(supabase_url=models.supabase_url, supabase_key=models.supabase_key)

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
            user_response = models.supabase.auth.sign_in_with_password({"email": email, "password": password})
            user_data = user_response.user
            session['user'] = {'id': user_data.id, 'email': user_data.email}
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
            res = models.supabase.auth.sign_up({"email": email, "password": password})
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

    # Create location-city map for the frontend
    location_city_map = {}
    for day in plan.days:
        for item in day.items:
            if item.location and item.location.name and item.location.city:
                location_city_map[item.location.name] = item.location.city

    amap_key = os.environ.get("AMAP_KEY")
    amap_security_key = os.environ.get("AMAP_SECURITY_KEY")
    return render_template('plan_details.html', plan=plan, is_details_view=True, amap_key=amap_key, amap_security_key=amap_security_key, location_city_map=location_city_map)

@app.route('/generate-plan', methods=['POST'])
@login_required
def generate_plan_route():
    query = request.form.get('query')
    if not query:
        flash("Please provide a query for your travel plan.", "danger")
        return redirect(url_for('index'))

    # Generate the plan using the LLM service
    plan_data = llm_service.generate_plan(query)

    if not plan_data:
        flash("Could not generate a plan based on your query. Please try again.", "danger")
        return redirect(url_for('index'))

    # Convert dictionary to TravelPlan object
    plan = _create_plan_object_from_dict(plan_data)

    # Create location-city map for the frontend
    location_city_map = {}
    for day in plan.days:
        for item in day.items:
            if item.location and item.location.name and item.location.city:
                location_city_map[item.location.name] = item.location.city
    
    # Store plan in session to be able to save it later
    session['generated_plan'] = plan.to_dict()
    
    amap_key = os.environ.get("AMAP_KEY")
    amap_security_key = os.environ.get("AMAP_SECURITY_KEY")
    return render_template('plan_result.html', plan=plan, is_details_view=False, amap_key=amap_key, amap_security_key=amap_security_key, location_city_map=location_city_map)

@app.route('/save-plan', methods=['POST'])
@login_required
def save_plan_route():
    if 'generated_plan' not in session:
        flash("No plan to save.", "danger")
        return redirect(url_for('index'))

    plan_data = session.pop('generated_plan', None)
    
    days = []
    location_map = {}
    for day_data in plan_data.get('days', []):
        items = []
        for item_data in day_data.get('items', []):
            location = None
            if item_data.get('location'):
                loc_data = item_data['location']
                if loc_data['id'] in location_map:
                    location = location_map[loc_data['id']]
                else:
                    location = models.Location(name=loc_data['name'], city=loc_data['city'])
                    location_map[loc_data['id']] = location
            
            start_time = datetime.fromisoformat(item_data['start_time']) if item_data.get('start_time') else None
            end_time = datetime.fromisoformat(item_data['end_time']) if item_data.get('end_time') else None

            actual_costs = []
            for cost_data in item_data.get('actual_costs', []):
                actual_costs.append(models.ActualCost(
                    name=cost_data['name'],
                    amount=cost_data['amount'],
                    currency=cost_data['currency']
                ))

            items.append(models.ItineraryItem(
                item_type=item_data['item_type'],
                description=item_data['description'],
                start_time=start_time,
                end_time=end_time,
                location=location,
                estimated_cost=item_data.get('estimated_cost', 0.0),
                estimated_cost_currency=item_data.get('estimated_cost_currency', 'USD'),
                actual_costs=actual_costs
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

@app.route('/itinerary-item/<item_id>/costs', methods=['POST'])
@login_required
def create_actual_cost_route(item_id):
    data = request.json
    cost = models.ActualCost(
        itinerary_item_id=item_id,
        name=data['name'],
        amount=float(data['amount']),
        currency=data['currency']
    )
    new_cost = models.create_actual_cost(cost)
    return jsonify({'success': True, 'cost': new_cost.to_dict()})

@app.route('/actual-cost/<cost_id>/delete', methods=['POST'])
@login_required
def delete_actual_cost_route(cost_id):
    models.delete_actual_cost(cost_id)
    return jsonify({'success': True})


@app.route('/itinerary-item/<item_id>/update', methods=['POST'])
@login_required
def update_itinerary_item_route(item_id):
    try:
        updates = request.json
        updated_item = models.update_itinerary_item(item_id, updates)
        return jsonify({'success': True, 'item': updated_item})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/itinerary-item/<item_id>/delete', methods=['POST'])
@login_required
def delete_itinerary_item_route(item_id):
    try:
        models.delete_itinerary_item(item_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/day/<day_id>/insert-and-reorder', methods=['POST'])
@login_required
def insert_and_reorder_route(day_id):
    try:
        data = request.json
        new_item_data = data.get('new_item_data')
        items_to_update = data.get('items_to_update')

        if new_item_data:
            models.insert_itinerary_item(day_id, new_item_data)

        if items_to_update:
            for item_update in items_to_update:
                models.update_itinerary_item(item_update['id'], {'order': item_update['order']})

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



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
