# routers/chat.py

from fastapi import APIRouter, Depends, HTTPException,File, UploadFile
from fastapi.responses import StreamingResponse
from gridfs import GridFS
from gridfs.errors import NoFile
from typing import List
from pydantic import BaseModel
from bson.objectid import ObjectId
from database import get_database
from pymongo import MongoClient
from bson import json_util
from bson import ObjectId
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from bson.json_util import dumps
import json
import uuid
import datetime


router = APIRouter()

class Message(BaseModel):
    sender_id: str
    content: str
    timestamp: datetime.datetime


class Chat(BaseModel):
    room_id: str
    user_id: str
    doctor_id: str
    messages: List[Message]

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)




@router.post("/chat/{room_id}/send")
async def send_message(room_id: str, message: Message, sender_id: str, db: MongoClient = Depends(get_database)):
    chats_collection = db["chats"]

    chat = chats_collection.find_one({"room_id": room_id})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat room not found")

    # Check if the user is authorized to send message in this appointment
    if sender_id not in [str(chat["user_id"]), str(chat["doctor_id"])]:
        raise HTTPException(status_code=403, detail="Unauthorized user")

    # Add a unique message ID to the message
    message_id = str(uuid.uuid4())
    message_dict = message.dict()
    message_dict['sender_id'] = ObjectId(sender_id)
    message_dict['message_id'] = message_id

    chats_collection.update_one(
        {"room_id": room_id},
        {"$push": {"messages": message_dict}}
    )

    return {"message_id": message_id, "message": "Message sent"}





@router.get("/{room_id}/messages")
async def get_messages(room_id: str, db: MongoClient = Depends(get_database)):
    chats_collection = db["chats"]
    users_collection = db["users"]
    doctors_collection = db["doctors"]

    pipeline = [
        {"$match": {"room_id": room_id}},
        {"$unwind": "$messages"},
        {"$lookup": {
            "from": "users",
            "localField": "messages.sender_id",
            "foreignField": "_id",
            "as": "user_info"
        }},
        {"$lookup": {
            "from": "doctors",
            "localField": "messages.sender_id",
            "foreignField": "_id",
            "as": "doctor_info"
        }},
        {"$project": {
            "_id": {"$toString": "$messages._id"},
            "sender_id": {"$toString": "$messages.sender_id"},
            "content": "$messages.content",
            "timestamp": {"$toString": "$messages.timestamp"},
            "user_info.name": 1,
            "doctor_info.name": 1,
        }}
    ]

    messages = chats_collection.aggregate(pipeline)
    messages = json.loads(json_util.dumps(messages))
    formatted_messages = []
    for message in messages:
        sender_name = None
        if message['user_info']:
            sender_name = message['user_info'][0]['name']
        elif message['doctor_info']:
            sender_name = message['doctor_info'][0]['name']
        formatted_message = {
            "_id": message["_id"],
            "sender_id": message["sender_id"],
            "content": message["content"],
            "timestamp": message["timestamp"],
            "sender_name": sender_name
        }
        formatted_messages.append(formatted_message)
    
    return {"messages": formatted_messages}



@router.delete("/chat/{room_id}/message/{message_id}")
async def delete_message(room_id: str, message_id: str, db: MongoClient = Depends(get_database)):
    chats_collection = db["chats"]

    result = chats_collection.update_one({"room_id": room_id}, {"$pull": {"messages": {"message_id": message_id}}})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")

    return {"message": "Message deleted successfully"}



@router.post("/chat/{room_id}/send-file")
async def send_file(room_id: str, sender_id: str, file: UploadFile = File(...), db: MongoClient = Depends(get_database)):
    chats_collection = db["chats"]
    chat = chats_collection.find_one({"room_id": room_id})

    if not chat:
        raise HTTPException(status_code=404, detail="Chat room not found")

    fs = GridFS(db)
    file_id = fs.put(await file.read(), filename=file.filename, content_type=file.content_type)

    message = {
        "sender_id": ObjectId(sender_id),
        "file_id": file_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "timestamp": datetime.datetime.utcnow(),
    }

    chats_collection.update_one({"room_id": room_id}, {"$push": {"messages": message}})
    return {"message": "File sent"}


@router.get("/chat/{room_id}/download-file/{file_id}")
async def download_file(room_id: str, file_id: str, db: MongoClient = Depends(get_database)):
    chats_collection = db["chats"]
    chat = chats_collection.find_one({"room_id": room_id})

    if not chat:
        raise HTTPException(status_code=404, detail="Chat room not found")

    fs = GridFS(db)

    try:
        file = fs.get(ObjectId(file_id))
    except NoFile:
        raise HTTPException(status_code=404, detail="File not found")

    return StreamingResponse(file, media_type=file.content_type, headers={"Content-Disposition": f"attachment; filename={file.filename}"})

@router.delete("/chat/{room_id}/delete-file/{file_id}")
async def delete_file(room_id: str, file_id: str, db: MongoClient = Depends(get_database)):
    chats_collection = db["chats"]
    chat = chats_collection.find_one({"room_id": room_id})

    if not chat:
        raise HTTPException(status_code=404, detail="Chat room not found")

    fs = GridFS(db)

    try:
        fs.delete(ObjectId(file_id))
    except NoFile:
        raise HTTPException(status_code=404, detail="File not found")

    # Remove the file reference from the chat room's messages
    chats_collection.update_one({"room_id": room_id}, {"$pull": {"messages": {"file_id": ObjectId(file_id)}}})

    return {"message": "File deleted"}
