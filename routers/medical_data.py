# routers/medical_data.py

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Response
from bson.objectid import ObjectId
from pydantic import BaseModel
from typing import Optional
from database import get_database
from pymongo import MongoClient
from bson import json_util
import json
from gridfs import GridFS
from gridfs.errors import NoFile

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


@router.post("/medical-data/{user_id}/upload-file")
async def upload_medical_file(user_id: str, file: UploadFile = File(...), db: MongoClient = Depends(get_database)):
    fs = GridFS(db)
    user_files = fs.find({"user_id": ObjectId(user_id)})
    for uf in user_files:
        if uf.filename == file.filename:
            raise HTTPException(status_code=400, detail="File already exists")
    fs.put(file.file, filename=file.filename, user_id=ObjectId(user_id))
    return {"filename": file.filename}

@router.get("/medical-data/{user_id}/file/{filename}")
async def get_medical_file(user_id: str, filename: str, db: MongoClient = Depends(get_database)):
    fs = GridFS(db)
    user_file = fs.find_one({"user_id": ObjectId(user_id), "filename": filename})
    if user_file is None:
        raise NoFile("File not found")
    response = Response(content=user_file.read(), media_type='application/octet-stream')
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response

@router.get("/medical-data/{user_id}/files")
async def get_medical_files_by_user_id(user_id: str, db: MongoClient = Depends(get_database)):
    fs = GridFS(db)
    user_files = fs.find({"user_id": ObjectId(user_id)})
    files_list = []
    for file in user_files:
        file_dict = {
            "file_id": str(file._id),
            "user_id": str(file.user_id),
            "filename": file.filename,
            "uploadDate": file.upload_date
        }
        files_list.append(file_dict)
    return files_list


@router.get("/medical-data/{user_id}/file/{file_id}/{filename}")
async def download_medical_file(user_id: str, file_id: str, filename: str, db: MongoClient = Depends(get_database)):
    fs = GridFS(db)
    user_file = fs.find_one({"_id": ObjectId(file_id), "user_id": ObjectId(user_id), "filename": filename})
    if user_file is None:
        raise HTTPException(status_code=404, detail="Medical file not found")
    response = Response(content=user_file.read(), media_type='application/octet-stream')
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response
