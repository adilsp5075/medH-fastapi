# routers/appointments.py

from fastapi import APIRouter,HTTPException,Depends
from pymongo import MongoClient
from bson import json_util, ObjectId
from database import get_database
from pydantic import BaseModel
import json
import datetime

# Connect to MongoDB
db = get_database()
appointments_collection = db["appointments"]
users_collection = db["users"] 
doctors_collection = db["doctors"]

router = APIRouter()

class Appointment(BaseModel):
    user_id: str
    doctor_id: str
    appointment_time: datetime.datetime
    doctor_name: str
    doctor_speciality: str
    notes: str
    status: str = "pending"
    chat_room_id: str = None

@router.get("/appointments")
async def get_appointments():
    appointments = appointments_collection.find()
    return json.loads(json_util.dumps(appointments))

@router.get("/appointments/{appointment_id}")
async def get_appointment(appointment_id: str):
    appointment = appointments_collection.find_one({"_id": ObjectId(appointment_id)})
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return json.loads(json_util.dumps(appointment))

@router.post("/appointments")
async def create_appointment(appointment: Appointment):
    appointment_dict = appointment.dict()
    appointment_dict['user_id'] = ObjectId(appointment_dict['user_id'])
    appointment_dict['doctor_id'] = ObjectId(appointment_dict['doctor_id'])
    result = appointments_collection.insert_one(appointment_dict)
    return {"id": str(result.inserted_id)}

@router.put("/appointments/{appointment_id}")
async def update_appointment(appointment_id: str, appointment: Appointment):
    appointment_dict = appointment.dict()
    appointment_dict['user_id'] = ObjectId(appointment_dict['user_id'])
    appointment_dict['doctor_id'] = ObjectId(appointment_dict['doctor_id'])
    result = appointments_collection.update_one({"_id": ObjectId(appointment_id)}, {"$set": appointment_dict})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"id": appointment_id}

@router.delete("/appointments/{appointment_id}")
async def delete_appointment(appointment_id: str):
    result = appointments_collection.delete_one({"_id": ObjectId(appointment_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"id": appointment_id}


@router.post("/book_appointment")
async def book_appointment(appointment: Appointment):
    # Check if the user and doctor exist
    user = users_collection.find_one({"_id": ObjectId(appointment.user_id)})
    doctor = doctors_collection.find_one({"_id": ObjectId(appointment.doctor_id)})
    if user is None or doctor is None:
        raise HTTPException(status_code=400, detail="Invalid user or doctor ID")

    # Check if the appointment time is available for the doctor
    existing_appointment = appointments_collection.find_one({
        "doctor_id": appointment.doctor_id,
        "appointment_time": appointment.appointment_time
    })
    if existing_appointment is not None:
        raise HTTPException(status_code=409, detail="The appointment time is not available")
    
    # If the doctor is not found, raise an HTTPException with status code 404 (Not Found)
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # Otherwise, create a new appointment object and insert it into MongoDB
    appointment_dict = appointment.dict()
    result = appointments_collection.insert_one(appointment_dict)

    # Return the ID of the newly created appointment object
    return {"id": str(result.inserted_id)}




@router.put("/appointments/{appointment_id}/accept")
async def accept_appointment(appointment_id: str, db: MongoClient = Depends(get_database)):
    appointments_collection = db["appointments"]
    appointment = appointments_collection.find_one({"_id": ObjectId(appointment_id)})
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment["status"] != "pending":
        raise HTTPException(status_code=400, detail="Appointment has already been processed")

    chat_room_id = f"chat-{appointment_id}"
    appointments_collection.update_one({"_id": ObjectId(appointment_id)}, {"$set": {"status": "accepted", "chat_room_id": chat_room_id}})

    return {"message": "Appointment accepted and chat room created", "chat_room_id": chat_room_id}




@router.put("/appointments/{appointment_id}/reject")
async def reject_appointment(appointment_id: str):
    appointment = appointments_collection.find_one({"_id": ObjectId(appointment_id)})
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment["status"] != "pending":
        raise HTTPException(status_code=400, detail="Appointment has already been processed")

    appointments_collection.update_one({"_id": ObjectId(appointment_id)}, {"$set": {"status": "rejected"}})

    return {"message": "Appointment rejected successfully"}
