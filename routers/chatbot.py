# routers/chatbot.py

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class UserMessage(BaseModel):
    text: str

class BotResponse(BaseModel):
    text: str

@router.post("/chatbot/message", response_model=BotResponse)
async def chatbot_message(user_message: UserMessage):
    response = process_message(user_message.text)
    return {"text": response}

def process_message(user_input: str) -> str:
    user_input = user_input.strip().lower()

    if user_input == "hello":
        return "Hello! How can I help you today?"

    return "I'm not sure how to respond to that. Please try something else."
