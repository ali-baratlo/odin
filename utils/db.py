import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
from .logger import logger

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "odin")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # The ismaster command is cheap and does not require auth.
    client.admin.command('ismaster')
    logger.info("Successfully connected to MongoDB.")
except ConnectionFailure as e:
    logger.critical(f"Failed to connect to MongoDB: {e}", exc_info=True)
    # This exception will be caught during startup
    raise

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