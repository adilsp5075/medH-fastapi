from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from bson import json_util, ObjectId
from database import get_database
from pydantic import BaseModel
import json
from bson.json_util import dumps
from datetime import datetime

router = APIRouter()

# Connect to MongoDB
db = get_database()
appointments_collection = db["appointments"]

class Notification(BaseModel):
    username: str
    doctorname: str
    appointment_time: datetime
    status: str

@router.get("/notifications")
async def list_notifications():
    notifications = appointments_collection.find({"status": "accepted"})
    notifications = json.loads(dumps(notifications))  # Convert BSON to JSON
    for notification in notifications:
        notification["_id"] = str(notification["_id"]["$oid"])
        notification["user_id"] = str(notification["user_id"]["$oid"])
        notification["doctor_id"] = str(notification["doctor_id"]["$oid"])
        if isinstance(notification["appointment_time"], dict) and "$date" in notification["appointment_time"]:
            notification["appointment_time"] = str(notification["appointment_time"]["$date"])
    return notifications


@router.get("/notifications/user/{user_id}")
async def list_notifications_by_user(user_id: str):
    notifications = appointments_collection.find({
        "user_id": ObjectId(user_id),
        "status": "accepted"
    })
    notifications = json.loads(dumps(notifications))  # Convert BSON to JSON
    for notification in notifications:
        notification["_id"] = str(notification["_id"]["$oid"])
        notification["user_id"] = str(notification["user_id"]["$oid"])
        notification["doctor_id"] = str(notification["doctor_id"]["$oid"])
        if isinstance(notification["appointment_time"], dict) and "$date" in notification["appointment_time"]:
            notification["appointment_time"] = str(notification["appointment_time"]["$date"])
    return notifications


@router.get("/notifications/user/{user_id}/count")
async def count_notifications_by_user(user_id: str):
    count = appointments_collection.count_documents({
        "user_id": ObjectId(user_id),
        "status": {"$in": ["accepted", "rejected"]}
    })
    return {"count": count}

