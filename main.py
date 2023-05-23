from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import users, doctors, chat, chatbot, appointments,medical_data,notification, prescriptions

app = FastAPI()

# Add the following line after including the users and doctors routers
app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(doctors.router, prefix="/api",tags=["doctors"])
app.include_router(appointments.router, prefix="/api",tags=["appointments"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(chatbot.router, prefix="/api",tags=["chatbot"])  
app.include_router(medical_data.router, prefix="/api", tags=["medical_data"])
app.include_router(notification.router, prefix="/api", tags=["notification"])
app.include_router(prescriptions.router, prefix="/api",tags=["prescriptions"])

# Define the allowed origins for CORS
# origins = [
#     "http://localhost",
#     "http://localhost:8000",
#     "http://127.0.0.1",
#     "http://127.0.0.1:8000"
# ]

origins=["*"]

# Add the CORS middleware to the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Hello": "World"}