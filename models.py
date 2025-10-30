import uuid
from datetime import datetime

# In-memory database
db = {
    "users": {},
    "plans": {},
}

class User:
    def __init__(self, id, email):
        self.id = id
        self.email = email

    def to_dict(self):
        return {"id": self.id, "email": self.email}

class TravelPlan:
    def __init__(self, user_id, title, description="", items=None):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.title = title
        self.description = description
        self.created_at = datetime.utcnow()
        self.items = items if items else []

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "items": [item.to_dict() for item in self.items],
        }

class ItineraryItem:
    def __init__(self, item_type, description, start_time=None, end_time=None, location=None):
        self.id = str(uuid.uuid4())
        self.item_type = item_type
        self.description = description
        self.start_time = start_time
        self.end_time = end_time
        self.location = location

    def to_dict(self):
        return {
            "id": self.id,
            "item_type": self.item_type,
            "description": self.description,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "location": self.location.to_dict() if self.location else None,
        }

class Location:
    def __init__(self, name, latitude, longitude):
        self.name = name
        self.latitude = latitude
        self.longitude = longitude

    def to_dict(self):
        return {"name": self.name, "latitude": self.latitude, "longitude": self.longitude}

# --- User CRUD ---
def create_user(user):
    db["users"][user.id] = user
    return user

def get_user(user_id):
    return db["users"].get(user_id)

# --- Plan CRUD ---
def create_plan(plan):
    db["plans"][plan.id] = plan
    return plan

def get_plan(plan_id):
    return db["plans"].get(plan_id)

def get_plans_by_user(user_id):
    return [plan for plan in db["plans"].values() if plan.user_id == user_id]

def update_plan(plan_id, title, description):
    plan = db["plans"].get(plan_id)
    if plan:
        plan.title = title
        plan.description = description
    return plan

def delete_plan(plan_id):
    if plan_id in db["plans"]:
        del db["plans"][plan_id]
        return True
    return False
