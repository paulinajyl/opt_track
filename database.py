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

    # Create the table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS applications (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        name TEXT,
        application_date DATE,
        approval_date DATE,
        card_received_date DATE
    )
    ''')

    # Check if the 'card_received_date' column exists and add it if necessary
    cursor.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'applications' AND column_name = 'card_received_date') THEN
            ALTER TABLE applications ADD COLUMN card_received_date DATE;
        END IF;
    END $$;
    """)

    conn.commit()
    conn.close()
