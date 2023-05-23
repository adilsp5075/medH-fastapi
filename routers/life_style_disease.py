from fastapi import APIRouter
from pydantic import BaseModel
import pickle

router = APIRouter()

# Define a Pydantic model for each input format
class CancerModel(BaseModel):
    radius_mean: float
    area_mean: float
    perimeter_mean: float
    concavity_mean: float
    concave_points_mean: float

class DiabetesModel(BaseModel):
    pregnancies: int
    glucose: float
    blood_pressure: float
    bmi: float
    diabetes_pedigree_function: float
    age: int

class HeartModel(BaseModel):
    cp: int
    trestbps: int
    chol : int
    fbs : int
    restecg: int
    thalach : int
    exang : int

class LiverModel(BaseModel):
    Total_Bilirubin: float
    Direct_Bilirubin : float 
    Alkaline_Phosphotase: int
    Alamine_Aminotransferase: int
    Total_Protiens: float
    Albumin : float
    Albumin_and_Globulin_Ratio: float

class KidneyModel(BaseModel):
    bp : float
    sg : float
    al : float
    su : float
    rbc : str
    pc : str
    pcc: str



# Similarly, define models for Heart, Liver and Kidney

def load_model(filename):
    with open(filename, 'rb') as file:
        model = pickle.load(file, fix_imports=True, encoding='latin1')
    return model

@router.post('/predict_cancer')
async def predict_cancer(data: CancerModel):
    model = load_model("prediction/cancer.pkl")
    prediction = model.predict([[
        data.radius_mean,
        data.area_mean,
        data.perimeter_mean,
        data.concavity_mean,
        data.concave_points_mean
    ]])
    return {"prediction": int(prediction[0])}

@router.post('/predict_diabetes')
async def predict_diabetes(data: DiabetesModel):
    model = load_model("prediction/diabetes.pkl")
    prediction = model.predict([[
        data.pregnancies,
        data.glucose,
        data.blood_pressure,
        data.bmi,
        data.diabetes_pedigree_function,
        data.age
    ]])
    return {"prediction": int(prediction[0])}

@router.post('/predict_heart')
async def predict_heart_disease(data: HeartModel):
    model = load_model('prediction/heart.pkl')

    prediction = model.predict([[
        data.cp,
        data.trestbps,
        data.chol,
        data.fbs,
        data.restecg,
        data.thalach,
        data.exang
    ]])
    return {"prediction" : int(prediction[0])}

@router.post('/predict_liver')
async def predict_liver_disease(data: LiverModel):
    model = load_model("prediction/liver.pkl")
    prediction = model.predict([[
        data.Total_Bilirubin,
        data.Direct_Bilirubin,
        data.Alkaline_Phosphotase,
        data.Alamine_Aminotransferase,
        data.Total_Protiens,
        data.Albumin,
        data.Albumin_and_Globulin_Ratio
    ]])
    return{"prediction": int(prediction[0])}

