from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
load_dotenv()

uri = os.environ.get("MONGO_URI")

# Send a ping to confirm a successful connection
try:
    client = MongoClient(uri, server_api=ServerApi('1'))
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
    client = None

def get_database():
    if client:
        db = client["mydatabase"]
        return db
    else:
        raise ValueError("MongoDB client is not connected")
