from fastapi import APIRouter, HTTPException, Depends
from pymongo import MongoClient
from bson import json_util, ObjectId
from database import get_database
from pydantic import BaseModel
import json
from bson.json_util import dumps
from datetime import datetime
from routers.doctors import get_current_doctor
import uuid
from bson.json_util import default


router = APIRouter()

# Connect to MongoDB
db = get_database()
users_collection = db["users"]
doctors_collection = db["doctors"]
appointments_collection = db["appointments"]

class Appointment(BaseModel):
    username: str
    doctorname: str
    user_id: str
    doctor_id: str
    appointment_time: datetime
    notes: str
    status: str = "pending"



@router.post("/appointments")
async def book_appointment(appointment: Appointment):
    # Check if the user and doctor exist
    user = users_collection.find_one({"_id": ObjectId(appointment.user_id)})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    doctor = doctors_collection.find_one({"_id": ObjectId(appointment.doctor_id)})
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # Check if the appointment time is available
    existing_appointment = appointments_collection.find_one({
        "doctor_id": ObjectId(appointment.doctor_id),
        "appointment_time": appointment.appointment_time
    })
    if existing_appointment is not None:
        raise HTTPException(status_code=400, detail="Appointment time not available")

    # Book the appointment
    appointment_dict = appointment.dict()
    appointment_dict['doctor_id'] = ObjectId(appointment.doctor_id)
    appointment_dict['user_id'] = ObjectId(appointment.user_id)
    result = appointments_collection.insert_one(appointment_dict)

    return {"message": "Appointment booked successfully"}

@router.get("/appointments")
async def list_appointments():
    appointments = appointments_collection.find()
    return json.loads(json_util.dumps(appointments))  # Convert BSON to JSON

@router.patch("/appointments/{appointment_id}")
async def edit_appointment(payload: dict):
    appointment_id = payload["appointment_id"]
    new_appointment_time = payload["new_appointment_time"]
    new_notes = payload["new_notes"]
    
    appointment = appointments_collection.find_one({"_id": ObjectId(appointment_id)})
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Check if the new appointment time is available
    existing_appointment = appointments_collection.find_one({
        "doctor_id": appointment['doctor_id'],
        "appointment_time": new_appointment_time
    })
    if existing_appointment is not None:
        raise HTTPException(status_code=400, detail="Appointment time not available")

    result = appointments_collection.update_one(
        {"_id": ObjectId(appointment_id)}, 
        {"$set": {"appointment_time": new_appointment_time, "notes": new_notes}}
    )

    return {"message": "Appointment updated successfully"}


@router.delete("/appointments/{appointment_id}")
async def delete_appointment(appointment_id: str):
    result = appointments_collection.delete_one({"_id": ObjectId(appointment_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")

    return {"message": "Appointment deleted successfully"}

@router.put("/appointments/{appointment_id}/accept")
async def accept_appointment(
    appointment_id: str,
):
    appointment = appointments_collection.find_one({"_id": ObjectId(appointment_id)})
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment["status"] != "pending":
        raise HTTPException(status_code=400, detail="Invalid operation: appointment has already been processed")

    # Generate a chat room ID and save it to the appointment object
    room_id = str(uuid.uuid4())
    appointments_collection.update_one({"_id": ObjectId(appointment_id)}, {"$set": {"status": "accepted", "room_id": room_id}})

    # Create a new chat room for the appointment
    chats_collection = get_database()["chats"]
    chat = {"room_id": room_id, "user_id": appointment["user_id"], "doctor_id": appointment["doctor_id"], "messages": []}
    chats_collection.insert_one(chat)

    return {"message": "Appointment accepted successfully"}


@router.put("/appointments/{appointment_id}/reject")
async def reject_appointment(
    appointment_id: str,
):
    appointment = appointments_collection.find_one({"_id": ObjectId(appointment_id)})
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment["status"] != "pending":
        raise HTTPException(status_code=400, detail="Invalid operation: appointment has already been processed")

    appointments_collection.update_one({"_id": ObjectId(appointment_id)}, {"$set": {"status": "rejected"}})

    return {"message": "Appointment rejected successfully"}



@router.get("/appointments/{doctor_id}")
async def list_appointments_by_doctor(doctor_id: str):
    doctor = doctors_collection.find_one({"_id": ObjectId(doctor_id)})
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")

    appointments = appointments_collection.find({"doctor_id": ObjectId(doctor_id)})
    appointments = json.loads(dumps(appointments))  # Convert BSON to JSON
    for appointment in appointments:
        appointment["_id"] = str(appointment["_id"]["$oid"])
        appointment["user_id"] = str(appointment["user_id"]["$oid"])
        appointment["doctor_id"] = str(appointment["doctor_id"]["$oid"])
        if isinstance(appointment["appointment_time"], dict) and "$date" in appointment["appointment_time"]:
            appointment["appointment_time"] = str(appointment["appointment_time"]["$date"])

    return appointments


@router.get("/appointments/by-doctor/{doctor_id}")
async def get_appointments_by_doctor(doctor_id: str):
    doctor = doctors_collection.find_one({"_id": ObjectId(doctor_id)})
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")

    appointments = appointments_collection.find({"doctor_id": ObjectId(doctor_id)})
    return json.loads(json_util.dumps(appointments))  # Convert BSON to JSON


@router.get("/appointments/by-user/{user_id}")
async def get_appointments_by_user(user_id: str):
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    appointments = appointments_collection.find({"user_id": ObjectId(user_id)})
    appointments = json.loads(json_util.dumps(appointments))  # Convert BSON to JSON
    for appointment in appointments:
            appointment["_id"] = str(appointment["_id"]["$oid"])
            appointment["user_id"] = str(appointment["user_id"]["$oid"])
            appointment["doctor_id"] = str(appointment["doctor_id"]["$oid"])
            if isinstance(appointment["appointment_time"], dict) and "$date" in appointment["appointment_time"]:
                appointment["appointment_time"] = str(appointment["appointment_time"]["$date"])

    return appointments


@router.get("/appointments/by-status-user/{user_id}")
async def get_appointments_by_user(user_id: str):
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    appointments = appointments_collection.find({
        "user_id": ObjectId(user_id),
        "status": "accepted"
    })
    appointments = json.loads(json_util.dumps(appointments))  # Convert BSON to JSON
    for appointment in appointments:
        appointment["_id"] = str(appointment["_id"]["$oid"])
        appointment["user_id"] = str(appointment["user_id"]["$oid"])
        appointment["doctor_id"] = str(appointment["doctor_id"]["$oid"])
        if isinstance(appointment["appointment_time"], dict) and "$date" in appointment["appointment_time"]:
            appointment["appointment_time"] = str(appointment["appointment_time"]["$date"])

    return appointments
