#!/usr/bin/env python3
"""
CHEAT LMS - Simulated Learning Management System
Entry point for running the application
"""

import json
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import DATA_DIR, Config


def reset_database():
    """Delete the database to force fresh reload of courses."""
    db_path = DATA_DIR / "lms.db"
    if db_path.exists():
        db_path.unlink()
        print("Database reset. Courses will be reloaded from assessment files.")


def show_telemetry(user=None, limit=50, output_format="pretty"):
    """Display telemetry data from the log file."""
    log_file = Config.TELEMETRY_LOG_FILE

    if not log_file.exists():
        print("No telemetry data yet.")
        return

    entries = []
    with open(log_file, "r") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if user is None or entry.get("username") == user:
                    entries.append(entry)
            except json.JSONDecodeError:
                continue

    # Most recent first
    entries = list(reversed(entries[-limit:]))

    if not entries:
        print(f"No telemetry data found{f' for user {user}' if user else ''}.")
        return

    if output_format == "json":
        print(json.dumps(entries, indent=2))
    elif output_format == "jsonl":
        for entry in entries:
            print(json.dumps(entry))
    else:
        # Pretty print
        for entry in entries:
            ts = entry.get("timestamp_iso", "unknown")
            method = entry.get("method", "?")
            path = entry.get("path", "?")
            status = entry.get("status_code", "?")
            user = entry.get("username", "-")
            ua = entry.get("user_agent", "")[:60]
            duration = entry.get("duration_ms")
            duration_str = f"{duration:.0f}ms" if duration else "-"

            print(f"{ts}  {method:4} {path:40} {status}  {duration_str:>6}  {user:12} {ua}")

            # Show form data for POST requests (submissions)
            if method == "POST" and entry.get("form_data"):
                form = entry["form_data"]
                if "content" in form:
                    preview = form["content"][:100].replace("\n", " ")
                    print(f"           └─ content: {preview}...")
                elif any(k.startswith("question_") for k in form):
                    answers = {k: v for k, v in form.items() if k.startswith("question_")}
                    print(f"           └─ answers: {answers}")


def clear_telemetry():
    """Clear all telemetry data."""
    log_file = Config.TELEMETRY_LOG_FILE
    if log_file.exists():
        log_file.unlink()
        print("Telemetry data cleared.")
    else:
        print("No telemetry data to clear.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the CHEAT LMS server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--reload", action="store_true", help="Reset database and reload all courses from assessment files")

    # Telemetry commands
    parser.add_argument("--telemetry", action="store_true", help="Show telemetry data and exit")
    parser.add_argument("--telemetry-user", metavar="USER", help="Filter telemetry by username")
    parser.add_argument("--telemetry-limit", type=int, default=50, metavar="N", help="Number of entries to show (default: 50)")
    parser.add_argument("--telemetry-format", choices=["pretty", "json", "jsonl"], default="pretty", help="Output format")
    parser.add_argument("--telemetry-clear", action="store_true", help="Clear all telemetry data and exit")

    args = parser.parse_args()

    # Handle telemetry commands
    if args.telemetry_clear:
        clear_telemetry()
        sys.exit(0)

    if args.telemetry:
        show_telemetry(user=args.telemetry_user, limit=args.telemetry_limit, output_format=args.telemetry_format)
        sys.exit(0)

    # Normal server startup
    if args.reload:
        reset_database()

    from app import create_app
    app = create_app()

    print(f"\n{'='*50}")
    print("CHEAT LMS - Simulated Learning Management System")
    print(f"{'='*50}")
    print(f"\nServer running at: http://{args.host}:{args.port}")
    print("\nDemo accounts (password: student123):")
    print("  - jsmith")
    print("  - emartinez")
    print("  - twang")
    print(f"\n{'='*50}\n")

    app.run(host=args.host, port=args.port, debug=args.debug)
