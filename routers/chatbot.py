# routers/chatbot.py

from fastapi import APIRouter, HTTPException,Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import openai
from database import get_database
import pymongo

from scipy.stats import mode
import joblib

router = APIRouter()

# Load the saved models and data dictionary
final_rf_model, final_nb_model, final_svm_model, data_dict = joblib.load("prediction/prediction.pkl")

load_dotenv()
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Connect to MongoDB
db = get_database()
collection = db["predictions"]

class UserMessage(BaseModel):
    text: str

class BotResponse(BaseModel):
    text: str

class DiseasePrediction(BaseModel):
    symptoms: list
    location: dict

PROMPT = """Given the following symptoms, predict the most likely disease.
    
Symptoms:
{}
    
Disease prediction:"""


def generate_prediction(symptoms):
    if len(symptoms) < 3:
        raise HTTPException(status_code=400, detail="Please provide at least three symptoms.")

    # Format the prompt with the provided symptoms
    formatted_symptoms = "\n".join(symptoms)
    prompt = PROMPT.format(formatted_symptoms)

    # Generate prediction using OpenAI
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        temperature=0.3,
        max_tokens=60,
        top_p=1.0,
        frequency_penalty=0.5,
        presence_penalty=0.0,
    )

    # Parse response and return prediction
    prediction = response.choices[0].text.strip()
    return prediction

@router.post("/disease-prediction")
async def disease_prediction(disease_prediction: DiseasePrediction):
    symptoms = disease_prediction.symptoms
    prediction = generate_prediction(symptoms)
    
    # Save prediction and location in MongoDB
    record = {
        "symptoms": symptoms,
        "prediction": prediction,
        "location": disease_prediction.location
    }
    result = collection.insert_one(record)
    record_id = str(result.inserted_id)
    
     # Calculate count of disease predictions
    pipeline = [
        {"$group": {"_id": "$prediction", "count": {"$sum": 1}}}
    ]
    count_results = collection.aggregate(pipeline)
    disease_counts = {result["_id"]: result["count"] for result in count_results}
    
    return {"disease_prediction": prediction, "record_id": record_id, "disease_counts": disease_counts}



@router.post("/chatbot/message", response_model=BotResponse)
async def chatbot_message(user_message: UserMessage):
    response = process_message(user_message.text)
    return {"text": response}

def process_message(user_input: str) -> str:
    user_input = user_input.strip().lower()

    if user_input == "hello":
        return "Hello! How can I help you today?"

    return "I'm not sure how to respond to that. Please try something else."

# Define the predict endpoint
@router.post("/predict")
async def predict_disease(symptoms: str):
    # Split the symptoms input by commas and clean up any whitespace
    symptoms = [symptom.strip() for symptom in symptoms.split(",")]
    # Check if there are at least three symptoms
    if len(symptoms) < 3:
        return {"error": "Please enter at least three symptoms"}
    # Create a binary input vector for the input symptoms
    input_data = [0] * len(data_dict["symptom_index"])
    for symptom in symptoms:
        if symptom.capitalize() in data_dict["symptom_index"]:
            index = data_dict["symptom_index"][symptom.capitalize()]
            input_data[index] = 1
    # Make predictions using the saved models and take the mode of the predictions
    rf_prediction = data_dict["predictions_classes"][final_rf_model.predict([input_data])[0]]
    nb_prediction = data_dict["predictions_classes"][final_nb_model.predict([input_data])[0]]
    svm_prediction = data_dict["predictions_classes"][final_svm_model.predict([input_data])[0]]
    final_prediction = mode([rf_prediction, nb_prediction, svm_prediction])[0][0]
    # Save prediction in MongoDB
    record = {"symptoms": symptoms, "disease": final_prediction}
    result = collection.insert_one(record)
    record_id = str(result.inserted_id)
    # Return the final prediction
    return {"disease": final_prediction, "record_id": record_id}
