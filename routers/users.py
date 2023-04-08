# routers/users.py

from fastapi import APIRouter,HTTPException
from pymongo import MongoClient
from bson import json_util, ObjectId
from database import get_database
from pydantic import BaseModel
import json
import hashlib

# Connect to MongoDB
db = get_database()
users_collection = db["users"]

router = APIRouter()

class User(BaseModel):
    name: str
    username: str
    email: str
    password: str
    gender: str
    age: int

class UserLogin(BaseModel):
    email: str
    password: str

@router.get("/users")
async def get_users():
    users = users_collection.find()
    return json.loads(json_util.dumps(users))  # Convert BSON to JSON

@router.get("/users/{user_id}")
async def get_user(user_id: str):
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return json.loads(json_util.dumps(user))

@router.post("/register/user")
async def register_user(user: User):
    # Hash the password before saving it to the database
    hashed_password = hashlib.sha256(user.password.encode()).hexdigest()

    # Insert the user object into MongoDB
    user_dict = user.dict()
    user_dict['password'] = hashed_password
    result = users_collection.insert_one(user_dict)

    # Return the ID of the newly created user object
    return {"id": str(result.inserted_id)}

@router.post("/login/user")
async def login_user(user_login: UserLogin):
    # Hash the password before querying the database
    hashed_password = hashlib.sha256(user_login.password.encode()).hexdigest()

    # Find the user in MongoDB by email and hashed password
    user = users_collection.find_one({
        "email": user_login.email,
        "password": hashed_password
    })

    # If the user is not found, raise an HTTPException with status code 401 (Unauthorized)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Otherwise, return the user object with the "_id" field converted to a string
    user["_id"] = str(user["_id"])
    return {
        "user": user,
        "message": "Login successful"
    }