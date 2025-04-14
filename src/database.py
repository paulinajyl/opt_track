import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.environ['DATABASE_URL']

def get_connection():
    connection = psycopg2.connect(DATABASE_URL)
    print("Connection successful!")
    return connection

def setup_database():
    conn = get_connection()
    cursor = conn.cursor()

    # Unified table: applications with embedded user info
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS applications (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        user_name TEXT NOT NULL,
        premium_processing BOOLEAN,
        application_date TEXT,
        approval_date TEXT,
        card_produced_date TEXT,
        card_shipped_date TEXT,
        card_delivered_date TEXT
    )
    ''')

    conn.commit()
    conn.close()


def get_or_create_user(user_id, user_name=None):
    """Get or create an application record by user ID."""
    conn = get_connection()
    cursor = conn.cursor()

    # Check if an application exists for this user
    cursor.execute("SELECT user_name FROM applications WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()

    if result:
        user_name_result = result[0]
    elif user_name:
        # Create new application entry with user info
        cursor.execute(
            "INSERT INTO applications (user_id, user_name) VALUES (%s, %s)",
            (user_id, user_name)
        )
        conn.commit()
        user_name_result = user_name
    else:
        user_name_result = None

    conn.close()
    return user_name_result
