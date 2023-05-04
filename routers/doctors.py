# routers/doctors.py

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from pymongo import MongoClient
from bson import json_util, ObjectId
from database import get_database
from pydantic import BaseModel
from typing import Dict
import json
import hashlib
from datetime import datetime, timedelta
import jwt

# Secret key for JWT
SECRET_KEY = "justformedicalpurposeapplication"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Connect to MongoDB
db = get_database()
doctors_collection = db["doctors"]

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login/doctor")

class Doctor(BaseModel):
    name: str
    username: str
    email: str
    password: str
    speciality: str
    doc_id : str
    years_of_experience: int

class DoctorLogin(BaseModel):
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

@router.get("/doctors")
async def get_doctors():
    doctors = doctors_collection.find()
    doctors = json.loads(json_util.dumps(doctors))
    for doctor in doctors:
        doctor["_id"] = str(doctor["_id"]["$oid"])  # Remove curly braces from ObjectId string
    return doctors



@router.get("/doctors/{doctor_id}")
async def get_doctor(doctor_id: str):
    doctor = doctors_collection.find_one({"_id": ObjectId(doctor_id)})
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return json.loads(json_util.dumps(doctor))


@router.post("/register/doctor")
async def register_doctor(doctor: Doctor):
    # Hash the password before saving it to the database
    hashed_password = hashlib.sha256(doctor.password.encode()).hexdigest()

    # Insert the doctor object into MongoDB
    doctor_dict = doctor.dict()
    doctor_dict['password'] = hashed_password
    result = doctors_collection.insert_one(doctor_dict)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(result.inserted_id)}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login/doctor")
async def login_doctor(doctor_login: DoctorLogin):
    # Hash the password before querying the database
    hashed_password = hashlib.sha256(doctor_login.password.encode()).hexdigest()

    # Find the doctor in MongoDB by email and hashed password
    doctor = doctors_collection.find_one({
        "email": doctor_login.email,
        "password": hashed_password
    })

    # If the doctor is not found, raise an HTTPException with status code 401 (Unauthorized)
    if doctor is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(doctor["_id"])}, expires_delta=access_token_expires
    )

    # Return all doctor details
    doctor["_id"] = str(doctor["_id"])  # Convert ObjectId to string
    return {"access_token": access_token, "token_type": "bearer", "doctor": doctor}




async def get_current_doctor(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        doctor_id = payload.get("sub")
        if doctor_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    doctor = doctors_collection.find_one({"_id": ObjectId(doctor_id)})
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doctor["_id"] = str(doctor["_id"])
    return doctor


@router.delete("/doctors/{doctor_id}")
async def delete_doctor(doctor_id: str, current_doctor: dict = Depends(get_current_doctor)):
    try:
        # Verify if the doctor_id matches the current_doctor's ID
        if str(current_doctor["_id"]) != doctor_id:
            raise HTTPException(status_code=403, detail="Forbidden: You can only delete your own account")

        result = doctors_collection.delete_one({"_id": ObjectId(doctor_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Doctor not found")

        return {"message": "Doctor deleted successfully"}
    except Exception as e:
        print(f"Error deleting doctor: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/logout/doctor")
async def logout_doctor(current_doctor: Doctor = Depends(get_current_doctor)):
    return {"message": "Logout successful"}

#get current doctor
@router.get("/doctor")
async def get_current_doctor(current_doctor: dict = Depends(get_current_doctor)):
    return current_doctor

