# routers/medical_data.py

from fastapi import APIRouter, Depends, HTTPException
from bson.objectid import ObjectId
from pydantic import BaseModel
from typing import Optional
from database import get_database
from pymongo import MongoClient
from bson import json_util
import json

router = APIRouter()

class MedicalRecord(BaseModel):
    user_id: str
    medical_history: Optional[str] = None
    blood_pressure: Optional[str] = None
    sugar_level: Optional[str] = None

@router.post("/medical-data")
async def add_medical_data(record: MedicalRecord, db: MongoClient = Depends(get_database)):
    medical_data_collection = db["medical_data"]
    record_dict = record.dict()
    record_dict['user_id'] = ObjectId(record_dict['user_id'])
    result = medical_data_collection.insert_one(record_dict)
    return {"_id": str(result.inserted_id)}

@router.patch("/medical-data/{record_id}")
async def update_medical_data(record_id: str, record: MedicalRecord, db: MongoClient = Depends(get_database)):
    medical_data_collection = db["medical_data"]
    record_dict = record.dict(exclude_unset=True)
    if 'user_id' in record_dict:
        record_dict['user_id'] = ObjectId(record_dict['user_id'])
    result = medical_data_collection.update_one({"_id": ObjectId(record_id)}, {"$set": record_dict})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Medical record not found or no changes made")
    return {"message": "Medical record updated"}

@router.get("/medical-data/{record_id}")
async def get_medical_data(record_id: str, db: MongoClient = Depends(get_database)):
    medical_data_collection = db["medical_data"]
    record = medical_data_collection.find_one({"_id": ObjectId(record_id)})
    if record is None:
        raise HTTPException(status_code=404, detail="Medical record not found")
    record["_id"] = str(record["_id"])
    record["user_id"] = str(record["user_id"])
    return record
