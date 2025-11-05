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

load_dotenv()

# --- App and Server Setup ---
app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- Mock AI Service ---
def generate_plan_mock(query):
    """Mocks a call to an AI service to generate a travel plan for Nanjing."""
    # Locations for the Nanjing Plan
    loc_nanjing_south_station = models.Location(name="南京南站", city="南京")
    loc_xinjiekou_station = models.Location(name="新街口站", city="南京")
    loc_ming_xiaoling = models.Location(name="明孝陵", city="南京")
    loc_meiling_palace = models.Location(name="美龄宫", city="南京")
    loc_nanjing_museum = models.Location(name="南京博物院", city="南京")
    loc_fuzimiao = models.Location(name="夫子庙秦淮风光带", city="南京")
    loc_memorial_hall = models.Location(name="侵华日军南京大屠杀遇难同胞纪念馆", city="南京")
    loc_presidential_palace = models.Location(name="总统府", city="南京")
    loc_jiming_temple = models.Location(name="古鸡鸣寺", city="南京")
    loc_taicheng = models.Location(name="台城", city="南京")
    loc_xuanwu_lake = models.Location(name="玄武湖公园", city="南京")

    # Day 1
    day1_items = [
        models.ItineraryItem(
            item_type="Transportation",
            description="从南京南站至酒店",
            start_time=datetime(2025, 11, 10, 10, 0),
            end_time=datetime(2025, 11, 10, 10, 30),
            location=loc_xinjiekou_station,
            estimated_cost=4.0,
            estimated_cost_currency="CNY",
            transportations=[
                models.Transportation(
                    transport_type="Public Transport",
                    start_location="南京南站",
                    end_location="新街口站",
                    estimated_time="30m",
                    estimated_cost=4.0
                )
            ]
        ),
        models.ItineraryItem(
            item_type="Hotel",
            description="酒店安顿",
            start_time=datetime(2025, 11, 10, 10, 30),
            end_time=datetime(2025, 11, 10, 11, 0),
            location=loc_xinjiekou_station,
            estimated_cost=0,
            estimated_cost_currency="CNY"
        ),
        models.ItineraryItem(
            item_type="Transportation",
            description="前往钟山风景区",
            start_time=datetime(2025, 11, 10, 11, 0),
            end_time=datetime(2025, 11, 10, 11, 40),
            location=loc_ming_xiaoling,
            estimated_cost=3.0,
            estimated_cost_currency="CNY",
            transportations=[
                models.Transportation(
                    transport_type="Public Transport",
                    start_location="新街口站",
                    end_location="明孝陵", # Simplified to attraction name
                    estimated_time="25m",
                    estimated_cost=3.0
                )
            ]
        ),
        models.ItineraryItem(
            item_type="Activity",
            description="游览明孝陵",
            start_time=datetime(2025, 11, 10, 11, 40),
            end_time=datetime(2025, 11, 10, 13, 0),
            location=loc_ming_xiaoling,
            estimated_cost=70.0,
            estimated_cost_currency="CNY"
        ),
        models.ItineraryItem(
            item_type="Transportation",
            description="景区内交通",
            start_time=datetime(2025, 11, 10, 13, 0),
            end_time=datetime(2025, 11, 10, 13, 20),
            location=loc_meiling_palace,
            estimated_cost=10.0,
            estimated_cost_currency="CNY",
            transportations=[
                models.Transportation(
                    transport_type="Driving", # Using Driving for "观光车"
                    start_location="明孝陵",
                    end_location="美龄宫",
                    estimated_time="10m",
                    estimated_cost=10.0
                )
            ]
        ),
        models.ItineraryItem(
            item_type="Activity",
            description="参观美龄宫",
            start_time=datetime(2025, 11, 10, 13, 20),
            end_time=datetime(2025, 11, 10, 14, 10),
            location=loc_meiling_palace,
            estimated_cost=30.0,
            estimated_cost_currency="CNY"
        ),
        models.ItineraryItem(
            item_type="Transportation",
            description="返回市区并用午餐",
            start_time=datetime(2025, 11, 10, 14, 10),
            end_time=datetime(2025, 11, 10, 14, 50),
            location=loc_xinjiekou_station,
            estimated_cost=53.0,
            estimated_cost_currency="CNY",
            transportations=[
                models.Transportation(
                    transport_type="Public Transport",
                    start_location="美龄宫",
                    end_location="新街口站",
                    estimated_time="40m",
                    estimated_cost=13.0
                )
            ]
        ),
        models.ItineraryItem(
            item_type="Activity",
            description="参观南京博物院",
            start_time=datetime(2025, 11, 10, 14, 50),
            end_time=datetime(2025, 11, 10, 18, 20),
            location=loc_nanjing_museum,
            estimated_cost=0,
            estimated_cost_currency="CNY",
            transportations=[
                models.Transportation(
                    transport_type="Public Transport",
                    start_location="新街口站",
                    end_location="南京博物院",
                    estimated_time="20m",
                    estimated_cost=2.0
                )
            ]
        ),
        models.ItineraryItem(
            item_type="Transportation",
            description="前往夫子庙",
            start_time=datetime(2025, 11, 10, 18, 20),
            end_time=datetime(2025, 11, 10, 19, 0),
            location=loc_fuzimiao,
            estimated_cost=3.0,
            estimated_cost_currency="CNY",
            transportations=[
                models.Transportation(
                    transport_type="Public Transport",
                    start_location="南京博物院",
                    end_location="夫子庙秦淮风光带",
                    estimated_time="40m",
                    estimated_cost=3.0
                )
            ]
        ),
        models.ItineraryItem(
            item_type="Activity",
            description="夫子庙夜游 & 晚餐",
            start_time=datetime(2025, 11, 10, 19, 0),
            end_time=datetime(2025, 11, 10, 21, 0),
            location=loc_fuzimiao,
            estimated_cost=180.0,
            estimated_cost_currency="CNY"
        ),
        models.ItineraryItem(
            item_type="Transportation",
            description="返回酒店",
            start_time=datetime(2025, 11, 10, 21, 0),
            end_time=datetime(2025, 11, 10, 21, 30),
            location=loc_xinjiekou_station,
            estimated_cost=3.0,
            estimated_cost_currency="CNY",
            transportations=[
                models.Transportation(
                    transport_type="Public Transport",
                    start_location="夫子庙秦淮风光带",
                    end_location="新街口站",
                    estimated_time="30m",
                    estimated_cost=3.0
                )
            ]
        )
    ]
    day1 = models.Day(date=datetime(2025, 11, 10).date(), items=day1_items)

    # Day 2
    day2_items = [
        models.ItineraryItem(
            item_type="Transportation",
            description="前往纪念馆",
            start_time=datetime(2025, 11, 11, 8, 30),
            end_time=datetime(2025, 11, 11, 9, 0),
            location=loc_memorial_hall,
            estimated_cost=3.0,
            estimated_cost_currency="CNY",
            transportations=[
                models.Transportation(
                    transport_type="Public Transport",
                    start_location="新街口站",
                    end_location="侵华日军南京大屠杀遇难同胞纪念馆",
                    estimated_time="30m",
                    estimated_cost=3.0
                )
            ]
        ),
        models.ItineraryItem(
            item_type="Activity",
            description="参观纪念馆",
            start_time=datetime(2025, 11, 11, 9, 0),
            end_time=datetime(2025, 11, 11, 11, 30),
            location=loc_memorial_hall,
            estimated_cost=0,
            estimated_cost_currency="CNY"
        ),
        models.ItineraryItem(
            item_type="Meal",
            description="午餐",
            start_time=datetime(2025, 11, 11, 11, 30),
            end_time=datetime(2025, 11, 11, 12, 30),
            location=loc_memorial_hall, # Assuming lunch near memorial hall
            estimated_cost=40.0,
            estimated_cost_currency="CNY"
        ),
        models.ItineraryItem(
            item_type="Transportation",
            description="前往总统府",
            start_time=datetime(2025, 11, 11, 12, 30),
            end_time=datetime(2025, 11, 11, 13, 0),
            location=loc_presidential_palace,
            estimated_cost=2.0,
            estimated_cost_currency="CNY",
            transportations=[
                models.Transportation(
                    transport_type="Public Transport",
                    start_location="侵华日军南京大屠杀遇难同胞纪念馆",
                    end_location="总统府",
                    estimated_time="30m",
                    estimated_cost=2.0
                )
            ]
        ),
        models.ItineraryItem(
            item_type="Activity",
            description="参观总统府",
            start_time=datetime(2025, 11, 11, 13, 0),
            end_time=datetime(2025, 11, 11, 15, 0),
            location=loc_presidential_palace,
            estimated_cost=35.0,
            estimated_cost_currency="CNY"
        ),
        models.ItineraryItem(
            item_type="Transportation",
            description="前往古鸡鸣寺",
            start_time=datetime(2025, 11, 11, 15, 0),
            end_time=datetime(2025, 11, 11, 15, 20),
            location=loc_jiming_temple,
            estimated_cost=2.0,
            estimated_cost_currency="CNY",
            transportations=[
                models.Transportation(
                    transport_type="Public Transport",
                    start_location="总统府",
                    end_location="古鸡鸣寺",
                    estimated_time="20m",
                    estimated_cost=2.0
                )
            ]
        ),
        models.ItineraryItem(
            item_type="Activity",
            description="游览古鸡鸣寺与台城",
            start_time=datetime(2025, 11, 11, 15, 20),
            end_time=datetime(2025, 11, 11, 17, 0),
            location=loc_taicheng,
            estimated_cost=40.0,
            estimated_cost_currency="CNY"
        ),
        models.ItineraryItem(
            item_type="Activity",
            description="玄武湖黄昏漫步",
            start_time=datetime(2025, 11, 11, 17, 0),
            end_time=datetime(2025, 11, 11, 18, 30),
            location=loc_xuanwu_lake,
            estimated_cost=0,
            estimated_cost_currency="CNY"
        ),
        models.ItineraryItem(
            item_type="Meal",
            description="晚餐 & 返回酒店取行李",
            start_time=datetime(2025, 11, 11, 18, 30),
            end_time=datetime(2025, 11, 11, 19, 30),
            location=loc_xinjiekou_station,
            estimated_cost=52.0,
            estimated_cost_currency="CNY",
            transportations=[
                models.Transportation(
                    transport_type="Public Transport",
                    start_location="玄武湖公园",
                    end_location="新街口站",
                    estimated_time="30m",
                    estimated_cost=2.0
                )
            ]
        ),
        models.ItineraryItem(
            item_type="Transportation",
            description="前往南京南站",
            start_time=datetime(2025, 11, 11, 19, 30),
            end_time=datetime(2025, 11, 11, 20, 0),
            location=loc_nanjing_south_station,
            estimated_cost=4.0,
            estimated_cost_currency="CNY",
            transportations=[
                models.Transportation(
                    transport_type="Public Transport",
                    start_location="新街口站",
                    end_location="南京南站",
                    estimated_time="30m",
                    estimated_cost=4.0
                )
            ]
        )
    ]
    day2 = models.Day(date=datetime(2025, 11, 11).date(), items=day2_items)

    # Create the travel plan
    plan = models.TravelPlan(
        user_id="mock_user",
        title=f"南京两日游：钟山风华与秦淮月夜",
        description="一份详细的南京两日游路线计划，从南京南站出发，涵盖历史与现代景观。",
        days=[day1, day2]
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

    # Generate the plan (mocked for now)
    plan = generate_plan_mock(query)

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

            transportations = []
            for trans_data in item_data.get('transportations', []):
                transportations.append(models.Transportation(
                    transport_type=trans_data['transport_type'],
                    start_location=trans_data['start_location'],
                    end_location=trans_data['end_location'],
                    estimated_time=trans_data['estimated_time'],
                    estimated_cost=trans_data['estimated_cost']
                ))

            items.append(models.ItineraryItem(
                item_type=item_data['item_type'],
                description=item_data['description'],
                start_time=start_time,
                end_time=end_time,
                location=location,
                estimated_cost=item_data.get('estimated_cost', 0.0),
                estimated_cost_currency=item_data.get('estimated_cost_currency', 'USD'),
                actual_costs=actual_costs,
                transportations=transportations
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

@app.route('/transportation/<transportation_id>/update', methods=['POST'])
@login_required
def update_transportation_route(transportation_id):
    updated_data = request.json
    updated_data.pop('plan_id', None) # Remove plan_id as it's not in the transportations table

    if 'estimated_cost' in updated_data:
        updated_data['estimated_cost'] = float(updated_data['estimated_cost'])

    models.update_transportation(transportation_id, updated_data)
    
    transportation = models.get_transportation(transportation_id)
    return jsonify({'success': True, 'transportation': transportation.to_dict()})

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
