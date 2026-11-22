
import sqlite3
from datetime import datetime

DATABASE_NAME = "data/tankertrack.db"


def get_connection():
    """Create a database connection."""
    return sqlite3.connect(DATABASE_NAME)


def initialize_database():
    """Create all required database tables."""

    connection = get_connection()
    cursor = connection.cursor()

    # Tanker Management Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tankers (
            tanker_id TEXT PRIMARY KEY,
            capacity INTEGER NOT NULL,
            current_water INTEGER NOT NULL,
            current_location TEXT NOT NULL,
            available INTEGER DEFAULT 1,
            status TEXT DEFAULT 'Available'
        )
    """)

    # Water Request Management Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            request_id TEXT PRIMARY KEY,
            area TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            priority TEXT NOT NULL,
            preferred_time TEXT,
            location TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            created_at TEXT
        )
    """)

    connection.commit()
    connection.close()


def add_tanker(tanker_id, capacity, current_water, location):
    """Add a new tanker."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO tankers
            (tanker_id, capacity, current_water, current_location)
            VALUES (?, ?, ?, ?)
        """, (tanker_id, capacity, current_water, location))

        connection.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        connection.close()


def get_all_tankers():
    """Retrieve all tankers."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM tankers")
    tankers = cursor.fetchall()

    connection.close()
    return tankers


def add_request(request_id, area, quantity, priority, preferred_time, location):
    """Register a new municipal water request."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO requests
            (request_id, area, quantity, priority, preferred_time,
             location, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            request_id,
            area,
            quantity,
            priority,
            preferred_time,
            location,
            datetime.now().isoformat(timespec="seconds")
        ))

        connection.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        connection.close()


def get_all_requests():
    """Retrieve all water requests."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM requests")
    requests = cursor.fetchall()

    connection.close()
    return requests


def update_request_status(request_id, status):
    """Update the status of a water request."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE requests
        SET status = ?
        WHERE request_id = ?
    """, (status, request_id))

    connection.commit()
    updated = cursor.rowcount > 0
    connection.close()

    return updated
