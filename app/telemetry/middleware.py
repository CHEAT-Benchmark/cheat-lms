import time
from flask import request, g
from flask_login import current_user

from app.telemetry.storage import log_request


def init_telemetry(app):
    """Initialize telemetry middleware on the Flask app."""

    @app.before_request
    def before_request():
        """Record request start time."""
        g.request_start_time = time.time()

    @app.after_request
    def after_request(response):
        """Log request telemetry after each request."""
        if not app.config.get("TELEMETRY_ENABLED", True):
            return response

        # Skip static files
        if request.path.startswith("/static"):
            return response

        # Calculate request duration
        duration_ms = None
        if hasattr(g, "request_start_time"):
            duration_ms = (time.time() - g.request_start_time) * 1000

        # Collect telemetry data
        telemetry_data = {
            "timestamp": time.time(),
            "method": request.method,
            "path": request.path,
            "full_url": request.url,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "user_agent": request.headers.get("User-Agent", ""),
            "ip_address": request.remote_addr,
            "referer": request.headers.get("Referer", ""),
            "user_id": current_user.id if current_user.is_authenticated else None,
            "username": current_user.username if current_user.is_authenticated else None,
            "request_headers": dict(request.headers),
            "query_params": dict(request.args),
            "content_type": request.content_type,
            "content_length": request.content_length,
        }

        # For POST requests, capture form data (excluding passwords)
        if request.method == "POST" and request.form:
            form_data = dict(request.form)
            # Redact sensitive fields
            for key in ["password", "current_password", "new_password"]:
                if key in form_data:
                    form_data[key] = "[REDACTED]"
            telemetry_data["form_data"] = form_data

        log_request(telemetry_data)

        return response

    return app
