
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
        # Schedule Generation History
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedule_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            generated_at TEXT NOT NULL,
            status TEXT DEFAULT 'Generated'
        )
    """)

    # Individual Tanker Assignments
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            request_id TEXT NOT NULL,
            tanker_id TEXT NOT NULL,
            start_minute INTEGER NOT NULL,
            delivery_time TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            location TEXT NOT NULL,
            FOREIGN KEY (run_id) REFERENCES schedule_runs(run_id)
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
def save_schedule(assignments):
    """Save a generated CSP schedule and its assignments."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        generated_at = datetime.now().isoformat(timespec="seconds")

        cursor.execute("""
            INSERT INTO schedule_runs (generated_at, status)
            VALUES (?, ?)
        """, (generated_at, "Generated"))

        run_id = cursor.lastrowid

        for request_id, assignment in assignments.items():

            cursor.execute("""
                INSERT INTO schedules (
                    run_id,
                    request_id,
                    tanker_id,
                    start_minute,
                    delivery_time,
                    quantity,
                    location
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                request_id,
                assignment.tanker_id,
                assignment.start_minute,
                assignment.display_time(),
                assignment.quantity,
                assignment.location
            ))

        connection.commit()
        return run_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_latest_schedule():
    """Retrieve the most recently generated schedule."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            request_id,
            tanker_id,
            delivery_time,
            quantity,
            location
        FROM schedules
        WHERE run_id = (
            SELECT MAX(run_id)
            FROM schedule_runs
        )
        ORDER BY start_minute
    """)

    results = cursor.fetchall()
    connection.close()

    return results

def get_schedule_history():
    """Retrieve all generated schedule runs."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            sr.run_id,
            sr.generated_at,
            sr.status,
            COUNT(s.schedule_id) AS total_assignments
        FROM schedule_runs sr
        LEFT JOIN schedules s
            ON sr.run_id = s.run_id
        GROUP BY sr.run_id
        ORDER BY sr.run_id DESC
    """)

    history = cursor.fetchall()
    connection.close()

    return history

def get_latest_schedule_for_simulation():
    """Load the latest saved schedule in MESA-compatible format."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            request_id,
            tanker_id,
            quantity,
            location,
            delivery_time
        FROM schedules
        WHERE run_id = (
            SELECT MAX(run_id)
            FROM schedule_runs
        )
        ORDER BY start_minute
    """)

    rows = cursor.fetchall()
    connection.close()

    assignments = []

    for row in rows:
        assignments.append({
            "request_id": row[0],
            "tanker_id": row[1],
            "quantity": row[2],
            "location": row[3],
            "delivery_time": row[4]
        })

    return assignments