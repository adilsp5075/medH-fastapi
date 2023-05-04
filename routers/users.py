# routers/users.py

import jwt
from fastapi import APIRouter, HTTPException, Depends, status, Header
from fastapi.security import OAuth2PasswordBearer
from pymongo import MongoClient
from bson import json_util, ObjectId
from typing import Optional
from database import get_database
from pydantic import BaseModel
import json
import hashlib
from datetime import datetime, timedelta
from utils.email import send_email

# Secret key for JWT
SECRET_KEY = "justformedicalpurposeapplication"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Connect to MongoDB
db = get_database()
users_collection = db["users"]

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login/user")

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

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

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

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(result.inserted_id)}, expires_delta=access_token_expires
    )

    # # Send welcome email to user
    # receiver_email = user.email
    # subject = "Welcome to our Medical App"
    # body = f"Hi {user.name},\n\nThank you for registering with our Medical App!"
    # send_email(receiver_email, subject, body)

    return {"access_token": access_token, "token_type": "bearer"}

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

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user["_id"])}, expires_delta=access_token_expires
    )


    # Return all user details
    user["_id"] = str(user["_id"])  # Convert ObjectId to string
    return {"access_token": access_token, "token_type": "bearer", "user": user}


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user["_id"] = str(user["_id"])
    return user


@router.post("/logout/user")
async def logout_user(token: str = Depends(oauth2_scheme)):
    # There's no server-side logout implementation with JWT. Simply delete the token client-side.
    return {"message": "Logout successful"}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str, 
    current_user: dict = Depends(get_current_user)
):
    # Verify if the user_id matches the current_user's ID
    if user_id != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Forbidden: You can only delete your own account")

    result = users_collection.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    

    # # Send deletion confirmation email to user
    # receiver_email = current_user["email"]
    # subject = "Account Deletion Confirmation"
    # body = f"Hi {current_user['name']},\n\nYour account with our Medical App has been successfully deleted at {datetime.utcnow()}."
    # send_email(receiver_email, subject, body)

    return {"message": "User deleted successfully"}

