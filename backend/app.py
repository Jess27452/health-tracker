from pathlib import Path
import sqlite3
from flask import Flask, jsonify, render_template, request


app = Flask(__name__, template_folder="templates", static_folder="static")

# Store the SQLite database file next to this app file.
BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "health_tracker.db"


def get_db_connection():
    """Create a connection to the SQLite database."""
    connection = sqlite3.connect(DATABASE)
    # This lets us access columns by name instead of only by index.
    connection.row_factory = sqlite3.Row
    return connection


def create_table():
    """Create the logs table if it does not already exist."""
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            sleep_hours REAL,
            stress_level INTEGER,
            mood TEXT,
            exercise_minutes INTEGER,
            food_notes TEXT,
            symptom_name TEXT,
            symptom_severity INTEGER,
            notes TEXT
        )
        """
    )

    connection.commit()
    connection.close()


def row_to_dict(row):
    """Convert one database row into a normal dictionary."""
    return dict(row)


@app.route("/", methods=["GET"])
def home():
    """Show the main page for the health tracker."""
    return render_template("index.html")


@app.route("/log", methods=["POST"])
def add_log():
    """Save one health log entry to the database."""
    data = request.get_json()

    # Basic validation so we always store a date for each entry.
    if not data or "date" not in data:
        return jsonify({"error": "The 'date' field is required."}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO logs (
            date,
            sleep_hours,
            stress_level,
            mood,
            exercise_minutes,
            food_notes,
            symptom_name,
            symptom_severity,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.get("date"),
            data.get("sleep_hours"),
            data.get("stress_level"),
            data.get("mood"),
            data.get("exercise_minutes"),
            data.get("food_notes"),
            data.get("symptom_name"),
            data.get("symptom_severity"),
            data.get("notes"),
        ),
    )

    connection.commit()
    new_id = cursor.lastrowid
    connection.close()

    return jsonify({"message": "Log saved successfully.", "id": new_id}), 201


@app.route("/logs", methods=["GET"])
def get_logs():
    """Return all health log entries as JSON."""
    connection = get_db_connection()
    cursor = connection.cursor()

    # Get every row from the logs table.
    cursor.execute("SELECT * FROM logs ORDER BY id DESC")
    rows = cursor.fetchall()
    connection.close()

    # Convert database rows into normal Python dictionaries.
    logs = [row_to_dict(row) for row in rows]
    return jsonify(logs)


# Create the table when the app starts, so the database is ready to use.
create_table()


if __name__ == "__main__":
    # Run the Flask development server.
    app.run(debug=True)
