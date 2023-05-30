from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
from tempfile import NamedTemporaryFile
from database import get_database
import shutil
import os

# Connect to MongoDB
db = get_database()
reports_collection = db["image_processing"]  # changed collection name

router = APIRouter()

def process_file(file_path):
    images = convert_from_path(file_path)
    if images:
        img = cv2.cvtColor(np.array(images[0]), cv2.COLOR_RGB2BGR)
    else:
        raise Exception("Could not convert PDF to image")

    # apply OCR to the image
    text = pytesseract.image_to_string(img)

    # Process the text
    lines = text.split('\n')

    report = {}
    for line in lines:
        if "patient name:" in line.lower():
            report['patient name'] = line.split(':')[-1].strip()
        elif "gender:" in line.lower():
            report['gender'] = line.split(':')[-1].strip()
        elif "age:" in line.lower():
            report['age'] = line.split(':')[-1].strip()
        elif "date and time" in line.lower():
            report['date and time'] = line.split(': ', 1)[-1].strip()
        elif "blood pressure:" in line.lower():
            report['blood pressure'] = line.split(':')[-1].strip()
        elif "sugar level:" in line.lower():
            report['sugar level'] = line.split(':')[-1].strip()
        elif "thyroid:" in line.lower():
            report['thyroid'] = line.split(':')[-1].strip()

    return report

@router.post("/uploadfile/{user_id}")
async def create_upload_file(user_id: str,file: UploadFile = File(...)):  # Add user_id parameter
    try:
        contents = await file.read()
        with NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(contents)
            temp_file.flush()
            temp_file.close()
            report = process_file(temp_file.name)
            os.unlink(temp_file.name)
            # add user_id to the report dictionary
            report["user_id"] = user_id
            # Insert the report into MongoDB
            result = reports_collection.insert_one(report)
            report["_id"] = str(result.inserted_id)  # convert ObjectId to string
            return report
    except Exception as e:
        return JSONResponse(status_code=400, content={"message": str(e)})
