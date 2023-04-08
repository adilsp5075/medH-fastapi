# database.py

from pymongo import MongoClient
from fastapi import Depends

def get_database():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["mydatabase"]
    return db
