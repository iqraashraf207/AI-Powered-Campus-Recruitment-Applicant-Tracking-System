import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

def get_db():
    """
    Creates and returns a PostgreSQL database connection.
    Use this function in every API endpoint that needs the database.
    """
    connection = psycopg2.connect(
        host     = os.getenv("DB_HOST"),
        port     = os.getenv("DB_PORT"),
        dbname   = os.getenv("DB_NAME"),
        user     = os.getenv("DB_USER"),
        password = os.getenv("DB_PASSWORD")
    )
    return connection


def get_cursor(connection):
    """
    Returns a cursor that gives results as dictionaries
    instead of plain tuples. Much easier to work with.
    Example: row["name"] instead of row[0]
    """
    return connection.cursor(cursor_factory=RealDictCursor)