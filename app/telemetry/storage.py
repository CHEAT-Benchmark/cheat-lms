import json
from datetime import datetime
from pathlib import Path

from app.config import Config


def log_request(data: dict):
    """Append telemetry data to the log file."""
    log_file = Config.TELEMETRY_LOG_FILE

    # Ensure parent directory exists
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # Add ISO timestamp for readability
    data["timestamp_iso"] = datetime.fromtimestamp(data["timestamp"]).isoformat()

    # Append as JSON line
    with open(log_file, "a") as f:
        f.write(json.dumps(data) + "\n")


def read_telemetry(limit: int = 100, user_id: int = None) -> list:
    """Read telemetry logs, optionally filtered by user."""
    log_file = Config.TELEMETRY_LOG_FILE

    if not Path(log_file).exists():
        return []

    entries = []
    with open(log_file, "r") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if user_id is None or entry.get("user_id") == user_id:
                    entries.append(entry)
            except json.JSONDecodeError:
                continue

    # Return most recent entries first
    return list(reversed(entries[-limit:]))


def get_user_sessions(user_id: int) -> list:
    """Group telemetry entries into sessions for a user."""
    entries = read_telemetry(limit=10000, user_id=user_id)

    sessions = []
    current_session = []
    last_timestamp = None
    session_gap = 30 * 60  # 30 minutes

    for entry in entries:
        timestamp = entry.get("timestamp", 0)

        if last_timestamp and (timestamp - last_timestamp) > session_gap:
            # Start new session
            if current_session:
                sessions.append(current_session)
            current_session = []

        current_session.append(entry)
        last_timestamp = timestamp

    if current_session:
        sessions.append(current_session)

    return sessions


def get_submission_telemetry(user_id: int, assignment_id: int) -> list:
    """Get all telemetry related to a specific assignment submission."""
    entries = read_telemetry(limit=10000, user_id=user_id)

    assignment_entries = []
    for entry in entries:
        path = entry.get("path", "")
        if f"/assignment/{assignment_id}" in path or f"/submit/" in path:
            assignment_entries.append(entry)

    return assignment_entries


def log_behavioral_event(event_data: dict):
    """Append a behavioral telemetry event to the log file."""
    log_file = Config.BEHAVIORAL_TELEMETRY_FILE

    # Ensure parent directory exists
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # Add ISO timestamp for readability
    if "timestamp" in event_data:
        event_data["timestamp_iso"] = datetime.fromtimestamp(
            event_data["timestamp"] / 1000
        ).isoformat()
    else:
        event_data["timestamp"] = int(datetime.now().timestamp() * 1000)
        event_data["timestamp_iso"] = datetime.now().isoformat()

    # Append as JSON line
    with open(log_file, "a") as f:
        f.write(json.dumps(event_data) + "\n")


def read_behavioral_telemetry(limit: int = 100) -> list:
    """Read behavioral telemetry logs."""
    log_file = Config.BEHAVIORAL_TELEMETRY_FILE

    if not Path(log_file).exists():
        return []

    entries = []
    with open(log_file, "r") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                entries.append(entry)
            except json.JSONDecodeError:
                continue

    # Return most recent entries first
    return list(reversed(entries[-limit:]))


def get_assignment_behavioral_data(user_id: int, assignment_id: int) -> list:
    """Retrieve behavioral telemetry for a specific assignment."""
    log_file = Config.BEHAVIORAL_TELEMETRY_FILE

    if not Path(log_file).exists():
        return []

    entries = []
    with open(log_file, "r") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if (
                    entry.get("user_id") == user_id
                    and entry.get("assignment_id") == assignment_id
                ):
                    entries.append(entry)
            except json.JSONDecodeError:
                continue

    return entries
