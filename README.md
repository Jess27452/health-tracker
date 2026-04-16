# Health Tracker

A beginner-friendly health tracker built with Flask and SQLite.

## What This Project Does

This project lets you:

- save a daily health log
- track sleep, stress, mood, exercise, food notes, symptoms, and extra notes
- view saved logs in a simple web page

## Project Structure

```text
backend/
  app.py
  static/
    style.css
  templates/
    index.html
```

## Requirements

- Python 3
- Flask

## Install Flask

```bash
pip3 install flask
```

## Run the App

From the project folder, run:

```bash
python3 backend/app.py
```

Then open:

- `http://127.0.0.1:5000/` for the main app page
- `http://127.0.0.1:5000/logs` to view raw JSON data

## Features

### Homepage

The homepage includes:

- a form to add a new health log
- a list of saved logs
- a refresh button to reload saved entries

### API Routes

#### `POST /log`

Saves one health log entry.

Example JSON:

```json
{
  "date": "2026-04-16",
  "sleep_hours": 8,
  "stress_level": 3,
  "mood": "good",
  "exercise_minutes": 30,
  "food_notes": "salad",
  "symptom_name": "headache",
  "symptom_severity": 2,
  "notes": "felt okay"
}
```

#### `GET /logs`

Returns all saved health logs as JSON.

## Database

The app uses SQLite and automatically creates a database file here:

`backend/health_tracker.db`

It also creates the `logs` table automatically if it does not already exist.

## Notes

- this project is designed for learning and local development
- Flask runs in debug mode in `app.py`
- the SQLite database file is ignored by git
