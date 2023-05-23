# routers/prescriptions.py

from fpdf import FPDF
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from pymongo import MongoClient
from bson import json_util, ObjectId
from database import get_database
from pydantic import BaseModel
from typing import List
import json

# Connect to MongoDB
db = get_database()
prescriptions_collection = db["prescriptions"]

router = APIRouter()

class Prescription(BaseModel):
    user_id: str
    doctor_id: str
    username: str
    doctor_name: str
    symptoms: List[str]
    prescription: str
    disease_name: str
    status: bool 

class PrescriptionPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Prescription Details', 0, 1, 'C')

    def prescription_details(self, prescription):
        self.set_font('Arial', '', 12)
        self.cell(0, 10, f'Patient Name: {prescription["username"]}', 0, 1)
        self.cell(0, 10, f'Doctor Name: {prescription["doctor_name"]}', 0, 1)
        self.cell(0, 10, f'Disease: {prescription["disease_name"]}', 0, 1)
        self.cell(0, 10, f'Symptoms: {", ".join(prescription["symptoms"])}', 0, 1)
        self.cell(0, 10, f'Prescription: {prescription["prescription"]}', 0, 1)


@router.get("/download_prescription/{prescription_id}")
async def download_prescription(prescription_id: str):
    prescription = prescriptions_collection.find_one({"_id": ObjectId(prescription_id)})

    if prescription is None:
        raise HTTPException(status_code=404, detail="Prescription not found")

    prescription["_id"] = str(prescription["_id"])  # Remove curly braces from ObjectId string

    pdf = PrescriptionPDF()
    pdf.add_page()
    pdf.prescription_details(prescription)

    filename = f"prescription_{prescription_id}.pdf"
    pdf.output(filename)

    return FileResponse(filename, media_type='application/pdf', filename=filename)

@router.post("/prescriptions")
async def add_prescription(prescription: Prescription):
    # Insert the prescription object into MongoDB
    prescription_dict = prescription.dict()

    # If status is not provided, default to False
    if "status" not in prescription_dict:
        prescription_dict["status"] = False

    result = prescriptions_collection.insert_one(prescription_dict)

    return {"message": "Prescription added successfully", "id": str(result.inserted_id)}

@router.get("/prescriptions/{doctor_id}")
async def get_prescriptions(doctor_id: str):
    prescriptions = prescriptions_collection.find({"doctor_id": doctor_id})

    if prescriptions is None:
        raise HTTPException(status_code=404, detail="No prescriptions found")

    prescriptions = json.loads(json_util.dumps(prescriptions))
    for prescription in prescriptions:
        prescription["_id"] = str(prescription["_id"]["$oid"])  # Remove curly braces from ObjectId string

    return prescriptions


