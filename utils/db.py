import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "odin")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

def get_db():
    """
    Returns a reference to the MongoDB database instance.
    """
    return db

def get_resource_collection():
    """
    Returns a reference to the 'resources' collection in the database.
    """
    return db.resources

def get_audit_log_collection():
    """
    Returns a reference to the 'audit_logs' collection in the database.
    """
    return db.audit_logs