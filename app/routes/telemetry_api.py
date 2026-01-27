from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.telemetry.storage import log_behavioral_event

telemetry_api_bp = Blueprint("telemetry_api", __name__)


@telemetry_api_bp.route("/api/telemetry/events", methods=["POST"])
@login_required
def receive_events():
    """Receive and store behavioral telemetry events from the client."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        events = data.get("events", [])

        if not isinstance(events, list):
            return jsonify({"error": "Events must be a list"}), 400

        for event in events:
            # Attach user context
            event["user_id"] = current_user.id
            event["server_timestamp"] = int(__import__("time").time() * 1000)

            # Log each event
            log_behavioral_event(event)

        return jsonify({"status": "ok", "received": len(events)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
