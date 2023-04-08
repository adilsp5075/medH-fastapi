# routers/doctors.py

from fastapi import APIRouter,HTTPException
from pymongo import MongoClient
from bson import json_util,ObjectId
from database import get_database
from pydantic import BaseModel
import json
import hashlib

# Connect to MongoDB
db = get_database()
doctors_collection = db["doctors"]

router = APIRouter()

class Doctor(BaseModel):
    name: str
    username: str
    email: str
    password: str
    speciality: str
    hospital: str
    years_of_experience: int

class DoctorLogin(BaseModel):
    email: str
    password: str


@router.get("/doctors")
async def get_doctors():
    doctors = doctors_collection.find()
    return json.loads(json_util.dumps(doctors))  # Convert BSON to JSON

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

    # Return the ID of the newly created doctor object
    return {"id": str(result.inserted_id)}



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

    # Otherwise, return the doctor object with the "_id" field converted to a string
    doctor["_id"] = str(doctor["_id"])
    return {
        "doctor": doctor,
        "message": "Login successful"
    }
