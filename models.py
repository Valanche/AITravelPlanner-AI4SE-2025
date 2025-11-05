import os
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# --- Supabase Setup ---
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# --- Data Models ---

class User:
    def __init__(self, id, email):
        self.id = id
        self.email = email

    def to_dict(self):
        return {"id": self.id, "email": self.email}

class TravelPlan:
    def __init__(self, user_id, title, description="", days=None, id=None, created_at=None):
        self.id = id if id else str(uuid.uuid4())
        self.user_id = user_id
        self.title = title
        self.description = description
        self.created_at = created_at if created_at else datetime.now(timezone.utc).replace(microsecond=0)
        self.days = days if days else []

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "days": [day.to_dict() for day in self.days],
        }

class Day:
    def __init__(self, date, items=None, id=None, plan_id=None):
        self.id = id if id else str(uuid.uuid4())
        self.plan_id = plan_id
        self.date = date
        self.items = items if items else []

    def to_dict(self):
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'date': self.date.isoformat(),
            'items': [item.to_dict() for item in self.items]
        }

class ItineraryItem:
    def __init__(self, item_type, description, start_time=None, end_time=None, location_id=None, location=None, estimated_cost=0.0, estimated_cost_currency='USD', actual_costs=None, transportations=None, id=None, day_id=None):
        self.id = id if id else str(uuid.uuid4())
        self.day_id = day_id
        self.item_type = item_type
        self.description = description
        self.start_time = start_time
        self.end_time = end_time
        self.location_id = location_id
        self.location = location
        self.estimated_cost = estimated_cost
        self.estimated_cost_currency = estimated_cost_currency
        self.actual_costs = actual_costs if actual_costs else []
        self.transportations = transportations if transportations else []

    def to_dict(self):
        return {
            "id": self.id,
            "day_id": self.day_id,
            "item_type": self.item_type,
            "description": self.description,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "location_id": self.location_id,
            "location": self.location.to_dict() if self.location else None,
            "estimated_cost": self.estimated_cost,
            "estimated_cost_currency": self.estimated_cost_currency,
            "actual_costs": [cost.to_dict() for cost in self.actual_costs],
            "transportations": [transportation.to_dict() for transportation in self.transportations],
        }

class Location:
    def __init__(self, name, city, id=None):
        self.id = id if id else str(uuid.uuid4())
        self.name = name
        self.city = city

    def to_dict(self):
        return {"id": self.id, "name": self.name, "city": self.city}

class Transportation:
    def __init__(self, transport_type, start_location, end_location, estimated_time, estimated_cost, id=None, itinerary_item_id=None):
        self.id = id if id else str(uuid.uuid4())
        self.itinerary_item_id = itinerary_item_id
        self.transport_type = transport_type
        self.start_location = start_location
        self.end_location = end_location
        self.estimated_time = estimated_time
        self.estimated_cost = estimated_cost

    def to_dict(self):
        return {
            "id": self.id,
            "itinerary_item_id": self.itinerary_item_id,
            "transport_type": self.transport_type,
            "start_location": self.start_location,
            "end_location": self.end_location,
            "estimated_time": self.estimated_time,
            "estimated_cost": self.estimated_cost,
        }

class ActualCost:
    def __init__(self, name, amount, currency, id=None, itinerary_item_id=None):
        self.id = id if id else str(uuid.uuid4())
        self.itinerary_item_id = itinerary_item_id
        self.name = name
        self.amount = amount
        self.currency = currency

    def to_dict(self):
        return {
            "id": self.id,
            "itinerary_item_id": self.itinerary_item_id,
            "name": self.name,
            "amount": self.amount,
            "currency": self.currency,
        }

# --- Database CRUD ---

def create_plan(plan):
    # 1. Insert the plan
    plan_data = supabase.table('plans').insert({
        'id': plan.id,
        'user_id': plan.user_id,
        'title': plan.title,
        'description': plan.description
    }).execute()

    if not plan_data.data:
        raise Exception("Failed to create plan")

    # 2. Insert the days, locations, items and costs
    inserted_location_ids = set()
    for day in plan.days:
        day.plan_id = plan.id
        day_data = supabase.table('days').insert({
            'id': day.id,
            'plan_id': day.plan_id,
            'date': day.date.isoformat()
        }).execute()

        if not day_data.data:
            raise Exception("Failed to create day")

        for item in day.items:
            item.day_id = day.id
            
            # Create location if it exists
            if item.location and item.location.id not in inserted_location_ids:
                item.location_id = item.location.id
                supabase.table('locations').insert({
                    'id': item.location.id,
                    'name': item.location.name,
                    'city': item.location.city
                }).execute()
                inserted_location_ids.add(item.location.id)

            item_insert = {
                'id': item.id,
                'day_id': item.day_id,
                'item_type': item.item_type,
                'description': item.description,
                'start_time': item.start_time.isoformat() if item.start_time else None,
                'end_time': item.end_time.isoformat() if item.end_time else None,
                'location_id': item.location_id,
                'estimated_cost': item.estimated_cost,
                'estimated_cost_currency': item.estimated_cost_currency,
            }
            
            item_data = supabase.table('itinerary_items').insert(item_insert).execute()

            if not item_data.data:
                raise Exception("Failed to create itinerary item")

            for transportation in item.transportations:
                transportation.itinerary_item_id = item.id
                supabase.table('transportations').insert({
                    'id': transportation.id,
                    'itinerary_item_id': transportation.itinerary_item_id,
                    'transport_type': transportation.transport_type,
                    'start_location': transportation.start_location,
                    'end_location': transportation.end_location,
                    'estimated_time': transportation.estimated_time,
                    'estimated_cost': transportation.estimated_cost
                }).execute()

            for cost in item.actual_costs:
                cost.itinerary_item_id = item.id
                supabase.table('actual_costs').insert({
                    'id': cost.id,
                    'itinerary_item_id': cost.itinerary_item_id,
                    'name': cost.name,
                    'amount': cost.amount,
                    'currency': cost.currency
                }).execute()

    return plan

def get_plan(plan_id):
    plan_data = supabase.table('plans').select("*, days(*, itinerary_items(*, locations(*), actual_costs(*), transportations(*)))").eq('id', plan_id).single().execute()
    if not plan_data.data:
        return None

    return _dict_to_travel_plan(plan_data.data)

def get_plans_by_user(user_id):
    plans_data = supabase.table('plans').select("*, days(*, itinerary_items(*, locations(*), actual_costs(*), transportations(*)))").eq('user_id', user_id).execute()
    return [_dict_to_travel_plan(plan) for plan in plans_data.data]

def delete_plan(plan_id):
    # 1. Get the plan to retrieve location_ids
    plan = get_plan(plan_id)
    if not plan:
        return False
    location_ids = [item.location.id for day in plan.days for item in day.items if item.location]

    # 2. Delete the plan, which will cascade to days, itinerary_items, and actual_costs
    supabase.table('plans').delete().eq('id', plan_id).execute()

    # 3. Delete the now-orphaned locations
    if location_ids:
        supabase.table('locations').delete().in_('id', location_ids).execute()

    return True

def create_actual_cost(cost):
    data = supabase.table('actual_costs').insert(cost.to_dict()).execute()
    if not data.data:
        raise Exception("Failed to create actual cost")
    return ActualCost(
        id=data.data[0]['id'],
        itinerary_item_id=data.data[0]['itinerary_item_id'],
        name=data.data[0]['name'],
        amount=data.data[0]['amount'],
        currency=data.data[0]['currency']
    )

def get_actual_cost(cost_id):
    data = supabase.table('actual_costs').select("*").eq('id', cost_id).single().execute()
    if not data.data:
        return None
    return data.data

def delete_actual_cost(cost_id):
    supabase.table('actual_costs').delete().eq('id', cost_id).execute()
    return True

def update_transportation(transportation_id, updated_data):
    supabase.table('transportations').update(updated_data).eq('id', transportation_id).execute()
    return True

def get_transportation(transportation_id):
    data = supabase.table('transportations').select("*").eq('id', transportation_id).single().execute()
    if not data.data:
        return None
    
    trans_dict = data.data
    return Transportation(
        id=trans_dict['id'],
        itinerary_item_id=trans_dict['itinerary_item_id'],
        transport_type=trans_dict['transport_type'],
        start_location=trans_dict['start_location'],
        end_location=trans_dict['end_location'],
        estimated_time=trans_dict['estimated_time'],
        estimated_cost=trans_dict['estimated_cost']
    )

def _dict_to_travel_plan(plan_dict):
    days = []
    for day_dict in plan_dict.get('days', []):
        items = []
        for item_dict in day_dict.get('itinerary_items', []):
            location = None
            if item_dict.get('locations'):
                loc_dict = item_dict['locations']
                location = Location(
                    id=loc_dict['id'],
                    name=loc_dict['name'],
                    city=loc_dict['city']
                )
            
            actual_costs = []
            for cost_dict in item_dict.get('actual_costs', []):
                actual_costs.append(ActualCost(
                    id=cost_dict['id'],
                    itinerary_item_id=cost_dict['itinerary_item_id'],
                    name=cost_dict['name'],
                    amount=cost_dict['amount'],
                    currency=cost_dict['currency']
                ))

            transportations = []
            for trans_dict in item_dict.get('transportations', []):
                transportations.append(Transportation(
                    id=trans_dict['id'],
                    itinerary_item_id=trans_dict['itinerary_item_id'],
                    transport_type=trans_dict['transport_type'],
                    start_location=trans_dict['start_location'],
                    end_location=trans_dict['end_location'],
                    estimated_time=trans_dict['estimated_time'],
                    estimated_cost=trans_dict['estimated_cost']
                ))

            items.append(ItineraryItem(
                id=item_dict['id'],
                day_id=item_dict['day_id'],
                item_type=item_dict['item_type'],
                description=item_dict['description'],
                start_time=datetime.fromisoformat(item_dict['start_time']) if item_dict.get('start_time') else None,
                end_time=datetime.fromisoformat(item_dict['end_time']) if item_dict.get('end_time') else None,
                location=location,
                location_id=item_dict.get('location_id'),
                estimated_cost=item_dict.get('estimated_cost', 0.0),
                estimated_cost_currency=item_dict.get('estimated_cost_currency', 'USD'),
                actual_costs=actual_costs,
                transportations=transportations
            ))
        days.append(Day(
            id=day_dict['id'],
            plan_id=day_dict['plan_id'],
            date=datetime.fromisoformat(day_dict['date']).date(),
            items=items
        ))
    
    return TravelPlan(
        id=plan_dict['id'],
        user_id=plan_dict['user_id'],
        title=plan_dict['title'],
        description=plan_dict['description'],
        created_at=datetime.fromisoformat(plan_dict['created_at']),
        days=days
    )

# --- Database Schema Note ---
# You need to create the following tables in your Supabase project:
#
# 1. plans:
#    - id: uuid (Primary Key)
#    - user_id: uuid (Foreign Key to auth.users.id)
#    - title: text
#    - description: text
#    - created_at: timestampz (default: now())
#
# 2. days:
#    - id: uuid (Primary Key)
#    - plan_id: uuid (Foreign Key to plans.id, with cascading delete)
#    - date: date
#
# 3. locations:
#    - id: uuid (Primary Key)
#    - name: text
#    - city: text
#
# 4. itinerary_items:
#    - id: uuid (Primary Key)
#    - day_id: uuid (Foreign Key to days.id, with cascading delete)
#    - location_id: uuid (Foreign Key to locations.id)
#    - item_type: text
#    - description: text
#    - start_time: timestampz
#    - end_time: timestampz
#    - estimated_cost: float8
#    - estimated_cost_currency: text
#
# 5. actual_costs:
#    - id: uuid (Primary Key)
#    - itinerary_item_id: uuid (Foreign Key to itinerary_items.id, with cascading delete)
#    - name: text
#    - amount: float8
#    - currency: text
#
# 6. transportations:
#    - id: uuid (Primary Key)
#    - itinerary_item_id: uuid (Foreign Key to itinerary_items.id, with cascading delete)
#    - transport_type: text
#    - start_location: text
#    - end_location: text
#    - estimated_time: text
#    - estimated_cost: float8
#
# Make sure to enable Row Level Security (RLS) on these tables and create policies
# that allow users to access only their own data.