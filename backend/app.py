from pathlib import Path
import sqlite3
from flask import Flask, jsonify, render_template, request


app = Flask(__name__, template_folder="templates", static_folder="static")

# Store the SQLite database file next to this app file.
BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "health_tracker.db"
MIN_LOGS_FOR_INSIGHTS = 5


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


def safe_float(value):
    """Convert a value to float when possible."""
    if value in (None, ""):
        return None
    return float(value)


def safe_int(value):
    """Convert a value to int when possible."""
    if value in (None, ""):
        return None
    return int(value)


def average(values):
    """Return the average of a list, or None if it is empty."""
    if not values:
        return None
    return sum(values) / len(values)


def build_insights(logs):
    """
    Look for simple habit patterns in the saved logs.

    This is not a medical model. It uses basic averages so beginners can
    understand how the suggestion logic works.
    """
    if len(logs) < MIN_LOGS_FOR_INSIGHTS:
        return {
            "ready": False,
            "message": (
                f"Add at least {MIN_LOGS_FOR_INSIGHTS} logs before generating "
                "habit insights."
            ),
            "patterns": [],
            "suggestions": [],
        }

    patterns = []
    suggestions = []

    symptom_logs = [
        log for log in logs
        if log.get("symptom_name") and safe_int(log.get("symptom_severity")) is not None
    ]
    severe_symptom_logs = [
        log for log in symptom_logs if safe_int(log.get("symptom_severity")) >= 6
    ]

    all_sleep = [safe_float(log.get("sleep_hours")) for log in logs]
    all_sleep = [value for value in all_sleep if value is not None]
    severe_sleep = [safe_float(log.get("sleep_hours")) for log in severe_symptom_logs]
    severe_sleep = [value for value in severe_sleep if value is not None]

    if severe_sleep and all_sleep:
        avg_sleep = average(all_sleep)
        avg_severe_sleep = average(severe_sleep)
        if avg_sleep is not None and avg_severe_sleep is not None and avg_severe_sleep < avg_sleep - 1:
            patterns.append(
                f"On stronger symptom days, sleep averaged {avg_severe_sleep:.1f} hours "
                f"compared with {avg_sleep:.1f} hours overall."
            )
            suggestions.append(
                "Try protecting sleep on the nights before difficult days, because "
                "lower sleep appears alongside stronger symptoms in your logs."
            )

    all_stress = [safe_int(log.get("stress_level")) for log in logs]
    all_stress = [value for value in all_stress if value is not None]
    severe_stress = [safe_int(log.get("stress_level")) for log in severe_symptom_logs]
    severe_stress = [value for value in severe_stress if value is not None]

    if severe_stress and all_stress:
        avg_stress = average(all_stress)
        avg_severe_stress = average(severe_stress)
        if avg_stress is not None and avg_severe_stress is not None and avg_severe_stress > avg_stress + 1:
            patterns.append(
                f"Higher symptom severity appears with higher stress: {avg_severe_stress:.1f} "
                f"on strong symptom days versus {avg_stress:.1f} overall."
            )
            suggestions.append(
                "Stress management may help. Try adding a short walk, breathing break, "
                "or lighter workload on high-stress days."
            )

    all_exercise = [safe_int(log.get("exercise_minutes")) for log in logs]
    all_exercise = [value for value in all_exercise if value is not None]
    severe_exercise = [safe_int(log.get("exercise_minutes")) for log in severe_symptom_logs]
    severe_exercise = [value for value in severe_exercise if value is not None]

    if severe_exercise and all_exercise:
        avg_exercise = average(all_exercise)
        avg_severe_exercise = average(severe_exercise)
        if (
            avg_exercise is not None
            and avg_severe_exercise is not None
            and avg_severe_exercise < avg_exercise - 10
        ):
            patterns.append(
                f"Exercise was lower on stronger symptom days: {avg_severe_exercise:.0f} "
                f"minutes versus {avg_exercise:.0f} minutes overall."
            )
            suggestions.append(
                "A small amount of regular movement may be worth testing, even if it is "
                "just 10 to 20 minutes on most days."
            )

    symptom_counts = {}
    for log in symptom_logs:
        symptom_name = log["symptom_name"].strip().lower()
        symptom_counts[symptom_name] = symptom_counts.get(symptom_name, 0) + 1

    if symptom_counts:
        top_symptom = max(symptom_counts, key=symptom_counts.get)
        patterns.append(
            f"Your most frequently logged symptom so far is '{top_symptom}' "
            f"({symptom_counts[top_symptom]} times)."
        )
        suggestions.append(
            f"Keep tracking what happens before '{top_symptom}' shows up so the trend "
            "becomes clearer over time."
        )

    if not patterns:
        patterns.append(
            "You have enough data to start analyzing, but the habits and symptoms do not "
            "show a strong pattern yet."
        )
        suggestions.append(
            "Keep logging consistently for a few more days so the tracker can spot clearer trends."
        )

    return {
        "ready": True,
        "message": "Insights are based on simple patterns in your saved logs.",
        "patterns": patterns,
        "suggestions": suggestions,
    }


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


@app.route("/insights", methods=["GET"])
def get_insights():
    """Analyze saved logs and return simple habit suggestions."""
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM logs ORDER BY id DESC")
    rows = cursor.fetchall()
    connection.close()

    logs = [row_to_dict(row) for row in rows]
    return jsonify(build_insights(logs))


# Create the table when the app starts, so the database is ready to use.
create_table()


if __name__ == "__main__":
    # Run the Flask development server.
    app.run(debug=True)
