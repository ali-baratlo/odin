import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv
import os

load_dotenv("config")

def get_connection():
    """
    Establishes a connection to the PostgreSQL database.
    
    The function attempts to connect to the database using environment variables
    DB_HOST, DB_PORT, DB_NAME, DB_USER, and DB_PASSWORD. If these variables are
    not set, the function will fall back to default values of localhost, 5432,
    odin, odin, and odin respectively.
    
    If the connection is successful, the function returns a connection object.
    Otherwise, it prints an error message and returns None.
    
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "db"),
            port=os.getenv("DB_SERVICE_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "odin"),
            user=os.getenv("DB_USER", "odin"),
            password=os.getenv("DB_PASSWORD", "odin"),
        )
        print("Connected to DB")
        return conn
    except psycopg2.OperationalError as e:
        print("Failed to connect to DB : ")
        print(e)
        return None
 
 
# for test: 
# conn = psycopg2.connect(host='localhost',port='5432',dbname='odintest' ,user='odin' ,password='')