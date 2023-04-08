# routers/chat.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel
from bson.objectid import ObjectId
from database import get_database
from pymongo import MongoClient
from bson import json_util
import json
import datetime


router = APIRouter()

class Message(BaseModel):
    sender_id: str
    content: str
    timestamp: datetime.datetime


class Chat(BaseModel):
    room_id: str
    messages: List[Message]

@router.get("/chat/{room_id}")
async def get_chat(room_id: str, db: MongoClient = Depends(get_database)):
    chats_collection = db["chats"]

    chat = chats_collection.find_one({"room_id": room_id})

    if not chat:
        raise HTTPException(status_code=404, detail="Chat room not found")

    chat["_id"] = str(chat["_id"])
    return chat

@router.post("/chat/{room_id}/send")
async def send_message(room_id: str, message: Message, db: MongoClient = Depends(get_database)):
    chats_collection = db["chats"]

    chat = chats_collection.find_one({"room_id": room_id})

    if not chat:
        raise HTTPException(status_code=404, detail="Chat room not found")

    # Convert sender_id from str to ObjectId
    message_dict = message.dict()
    message_dict['sender_id'] = ObjectId(message_dict['sender_id'])

    chats_collection.update_one({"room_id": room_id}, {"$push": {"messages": message_dict}})

    return {"message": "Message sent"}



from bson import json_util
import json

@router.get("/{room_id}/messages")
async def get_messages(room_id: str, db: MongoClient = Depends(get_database)):
    chat_collection = db["chat"]
    users_collection = db["users"]
    doctors_collection = db["doctors"]

    pipeline = [
        {"$match": {"room_id": room_id}},
        {"$lookup": {
            "from": "users",
            "localField": "sender_id",
            "foreignField": "_id",
            "as": "user_info"
        }},
        {"$lookup": {
            "from": "doctors",
            "localField": "sender_id",
            "foreignField": "_id",
            "as": "doctor_info"
        }},
        {"$project": {
            "_id": 1,
            "sender_id": 1,
            "content": 1,
            "timestamp": 1,
            "user_info.name": 1,
            "doctor_info.name": 1,
        }}
    ]

    messages = chat_collection.aggregate(pipeline)
    messages = json.loads(json_util.dumps(messages))
    formatted_messages = []
    for message in messages:
        sender_name = None
        if message['user_info']:
            sender_name = message['user_info'][0]['name']
        elif message['doctor_info']:
            sender_name = message['doctor_info'][0]['name']
        formatted_message = {
            "_id": message["_id"]["$oid"],
            "sender_id": message["sender_id"]["$oid"],
            "content": message["content"],
            "timestamp": message["timestamp"]["$date"],
            "sender_name": sender_name
        }
        formatted_messages.append(formatted_message)
    
    return {"messages": formatted_messages}

@router.delete("/{room_id}/message/{message_id}")
async def delete_message(room_id: str, message_id: str, db: MongoClient = Depends(get_database)):
    chat_collection = db["chat"]

    message = chat_collection.find_one({"_id": ObjectId(message_id), "room_id": room_id})
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")

    chat_collection.delete_one({"_id": ObjectId(message_id), "room_id": room_id})
    return {"message": "Message deleted successfully"}

