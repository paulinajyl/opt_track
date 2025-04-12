import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.environ['DATABASE_URL']

# Fetch variables
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")


def get_connection():
    #return psycopg2.connect(DATABASE_URL)

    connection = psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME
    )
    print("Connection successful!")

    return connection


def setup_database():
    conn = get_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        name TEXT NOT NULL
    )
    ''')

    # Create applications table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS applications (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        name TEXT,
        application_type TEXT,
        premium_processing BOOLEAN,
        application_date DATE,
        approval_date DATE,
        card_produced_date DATE,
        card_shipped_date DATE,
        card_delivered_date DATE
    )
    ''')

    conn.commit()
    conn.close()

def get_or_create_user(user_id, name=None):
    """Get a user by ID or create a new one if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT name FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    
    if user:
        # User exists
        result = user[0]
    elif name:
        # Create new user
        cursor.execute("INSERT INTO users (user_id, name) VALUES (%s, %s)", (user_id, name))
        conn.commit()
        result = name
    else:
        # User doesn't exist and no name provided
        result = None
    
    conn.close()
    return result