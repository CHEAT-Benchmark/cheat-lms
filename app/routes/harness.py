import os
import re
import signal
import subprocess
import time
from datetime import datetime
from pathlib import Path
from shutil import which

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

from app import db
from app.config import BASE_DIR
from app.models.course import Course
from app.models.assignment import Assignment
from app.models.test_run import TestRun
from app.models.user import User
from app.models.submission import Submission, Answer, DiscussionPost
from app.telemetry.storage import read_telemetry, read_behavioral_telemetry

# Test user accounts (password: student123)
TEST_USERNAMES = ["jsmith", "emartinez", "twang"]


def clear_test_user_data():
    """Delete all submissions, answers, and discussion posts from test users."""
    test_users = User.query.filter(User.username.in_(TEST_USERNAMES)).all()
    test_user_ids = [u.id for u in test_users]

    if not test_user_ids:
        return

    # Delete answers (must delete before submissions due to foreign key)
    submissions = Submission.query.filter(Submission.user_id.in_(test_user_ids)).all()
    submission_ids = [s.id for s in submissions]
    if submission_ids:
        Answer.query.filter(Answer.submission_id.in_(submission_ids)).delete(synchronize_session=False)

    # Delete submissions
    Submission.query.filter(Submission.user_id.in_(test_user_ids)).delete(synchronize_session=False)

    # Delete discussion posts
    DiscussionPost.query.filter(DiscussionPost.user_id.in_(test_user_ids)).delete(synchronize_session=False)

    db.session.commit()

harness_bp = Blueprint("harness", __name__, url_prefix="/harness")

PROMPTS_DIR = BASE_DIR / "prompts"


def is_cloudflared_available():
    """Check if cloudflared is installed."""
    return which("cloudflared") is not None


def start_cloudflare_tunnel(port=5001):
    """Start cloudflared tunnel and return (pid, url) or (None, None) on failure."""
    if not is_cloudflared_available():
        return None, None

    try:
        proc = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", f"http://localhost:{port}", "--protocol", "http2"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        # Wait for URL to appear in output (usually within 10 seconds)
        url = None
        start_time = time.time()
        while time.time() - start_time < 15:  # 15 second timeout
            line = proc.stdout.readline()
            if not line:
                break
            match = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
            if match:
                url = match.group(0)
                break

        if url:
            return proc.pid, url
        else:
            # Failed to get URL, kill the process
            proc.terminate()
            return None, None

    except Exception as e:
        print(f"Failed to start tunnel: {e}")
        return None, None


def stop_cloudflare_tunnel(pid):
    """Stop a cloudflared tunnel by PID."""
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass  # Process already dead
        except Exception as e:
            print(f"Failed to stop tunnel: {e}")

# Available AI agents for testing
AVAILABLE_AGENTS = [
    {"id": "openai-operator", "name": "OpenAI Operator"},
    {"id": "claude-computer-use", "name": "Claude Computer Use"},
    {"id": "anthropic-claude", "name": "Anthropic Claude"},
    {"id": "other", "name": "Other Agent"},
]


def get_available_prompts():
    """Get list of available prompt files."""
    if not PROMPTS_DIR.exists():
        return []
    prompts = []
    for f in sorted(PROMPTS_DIR.glob("*.txt")):
        with open(f, "r") as fp:
            content = fp.read().strip()
        prompts.append(
            {
                "filename": f.name,
                "name": f.stem.replace("-", " ").replace("_", " ").title(),
                "preview": content[:100] + "..." if len(content) > 100 else content,
                "content": content,
            }
        )
    return prompts


def get_prompt_content(filename):
    """Read the content of a prompt file."""
    filepath = PROMPTS_DIR / filename
    if filepath.exists():
        with open(filepath, "r") as f:
            return f.read().strip()
    return ""


@harness_bp.route("/")
def setup():
    """Setup page for configuring a test run."""
    courses = Course.query.all()
    prompts = get_available_prompts()
    cloudflared_available = is_cloudflared_available()
    return render_template(
        "harness/setup.html",
        agents=AVAILABLE_AGENTS,
        courses=courses,
        prompts=prompts,
        cloudflared_available=cloudflared_available,
    )


@harness_bp.route("/start", methods=["POST"])
def start():
    """Start a new test run."""
    agent_id = request.form.get("agent")
    course_id = request.form.get("course")
    selected_prompts = request.form.getlist("prompts")

    if not agent_id or not course_id or not selected_prompts:
        flash("Please select an agent, course, and at least one prompt.", "error")
        return redirect(url_for("harness.setup"))

    # Find agent name
    agent_name = next(
        (a["name"] for a in AVAILABLE_AGENTS if a["id"] == agent_id), agent_id
    )

    # Clear all previous submissions from test users for a fresh start
    clear_test_user_data()

    # Start Cloudflare tunnel for external access
    # Use port from Flask config or default to 5001 (5000 conflicts with macOS AirPlay)
    from flask import current_app
    port = current_app.config.get('SERVER_PORT', 5001)
    tunnel_pid, tunnel_url = start_cloudflare_tunnel(port=port)

    if not tunnel_url:
        flash(
            "Warning: Could not start Cloudflare tunnel. External agents won't be able to access the LMS.",
            "error",
        )

    # Create test run
    test_run = TestRun(
        agent_name=agent_name,
        course_id=int(course_id),
        prompts=selected_prompts,
        status="running",
        tunnel_url=tunnel_url,
        tunnel_pid=tunnel_pid,
    )
    db.session.add(test_run)
    db.session.commit()

    return redirect(url_for("harness.run", run_id=test_run.id))


@harness_bp.route("/run/<int:run_id>")
def run(run_id):
    """Test runner page showing current prompt and instructions."""
    test_run = TestRun.query.get_or_404(run_id)

    if test_run.status == "completed":
        return redirect(url_for("harness.results", run_id=run_id))

    # Get assignments for the course
    assignments = Assignment.query.filter_by(course_id=test_run.course_id).all()

    if not assignments:
        flash("No assignments found for this course.", "error")
        return redirect(url_for("harness.setup"))

    # Calculate current position
    total_combinations = len(test_run.prompts) * len(assignments)
    current_position = (
        test_run.current_prompt_index * len(assignments)
        + test_run.current_assignment_index
        + 1
    )

    # Get current prompt and assignment
    if test_run.current_prompt_index < len(test_run.prompts):
        current_prompt_file = test_run.prompts[test_run.current_prompt_index]
        current_prompt_content = get_prompt_content(current_prompt_file)
        current_prompt_name = (
            current_prompt_file.replace(".txt", "")
            .replace("-", " ")
            .replace("_", " ")
            .title()
        )
    else:
        current_prompt_file = None
        current_prompt_content = None
        current_prompt_name = None

    if test_run.current_assignment_index < len(assignments):
        current_assignment = assignments[test_run.current_assignment_index]
    else:
        current_assignment = None

    return render_template(
        "harness/runner.html",
        test_run=test_run,
        assignments=assignments,
        current_prompt_file=current_prompt_file,
        current_prompt_content=current_prompt_content,
        current_prompt_name=current_prompt_name,
        current_assignment=current_assignment,
        current_position=current_position,
        total_combinations=total_combinations,
    )


@harness_bp.route("/run/<int:run_id>/next", methods=["POST"])
def next_combination(run_id):
    """Advance to the next prompt/assignment combination."""
    test_run = TestRun.query.get_or_404(run_id)
    assignments = Assignment.query.filter_by(course_id=test_run.course_id).all()

    # Advance to next combination
    test_run.current_assignment_index += 1
    if test_run.current_assignment_index >= len(assignments):
        test_run.current_assignment_index = 0
        test_run.current_prompt_index += 1

    # Check if we've completed all combinations
    if test_run.current_prompt_index >= len(test_run.prompts):
        test_run.status = "completed"
        test_run.completed_at = datetime.utcnow()
        # Stop the tunnel
        if test_run.tunnel_pid:
            stop_cloudflare_tunnel(test_run.tunnel_pid)

    db.session.commit()

    if test_run.status == "completed":
        return redirect(url_for("harness.results", run_id=run_id))

    return redirect(url_for("harness.run", run_id=run_id))


@harness_bp.route("/run/<int:run_id>/complete", methods=["POST"])
def complete_run(run_id):
    """Mark the test run as complete and go to results."""
    test_run = TestRun.query.get_or_404(run_id)

    # Stop the tunnel
    if test_run.tunnel_pid:
        stop_cloudflare_tunnel(test_run.tunnel_pid)

    test_run.status = "completed"
    test_run.completed_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for("harness.results", run_id=run_id))


@harness_bp.route("/results/<int:run_id>")
def results(run_id):
    """Results dashboard showing submission counts, grid, and timeline."""
    from app.models.submission import Submission

    test_run = TestRun.query.get_or_404(run_id)
    assignments = Assignment.query.filter_by(course_id=test_run.course_id).all()
    assignment_ids = [a.id for a in assignments]

    # Get actual submissions from database during test run period
    submissions_query = Submission.query.filter(
        Submission.assignment_id.in_(assignment_ids),
        Submission.submitted_at >= test_run.started_at,
    )
    if test_run.completed_at:
        submissions_query = submissions_query.filter(
            Submission.submitted_at <= test_run.completed_at
        )

    # Build set of assignment IDs that were submitted
    submitted_assignment_ids = {s.assignment_id for s in submissions_query.all()}

    # Get submission count
    submission_count = len(submitted_assignment_ids)

    # Get telemetry for timeline
    # Use calendar.timegm to correctly interpret UTC datetimes as timestamps
    import calendar
    start_ts = calendar.timegm(test_run.started_at.timetuple()) if test_run.started_at else 0
    end_ts = (
        calendar.timegm(test_run.completed_at.timetuple())
        if test_run.completed_at
        else time.time()
    )

    # Merge request and behavioral telemetry
    request_telemetry = read_telemetry(limit=500)
    behavioral_telemetry = read_behavioral_telemetry(limit=500)

    timeline = []

    for entry in request_telemetry:
        ts = entry.get("timestamp", 0)
        if start_ts <= ts <= end_ts:
            timeline.append(
                {
                    "type": "request",
                    "timestamp": ts,
                    "timestamp_iso": entry.get("timestamp_iso", ""),
                    "method": entry.get("method", ""),
                    "path": entry.get("path", ""),
                    "status_code": entry.get("status_code", ""),
                    "username": entry.get("username", ""),
                }
            )

    for entry in behavioral_telemetry:
        ts = entry.get("server_timestamp", 0) / 1000  # Convert ms to seconds
        if start_ts <= ts <= end_ts:
            timeline.append(
                {
                    "type": "behavioral",
                    "timestamp": ts,
                    "event_type": entry.get("eventType", ""),
                    "data": entry.get("data", {}),
                }
            )

    # Sort timeline by timestamp
    timeline.sort(key=lambda x: x["timestamp"])

    return render_template(
        "harness/results.html",
        test_run=test_run,
        assignments=assignments,
        submitted_assignment_ids=submitted_assignment_ids,
        submission_count=submission_count,
        timeline=timeline,
    )


@harness_bp.route("/api/runs")
def list_runs():
    """API endpoint to list all test runs."""
    runs = TestRun.query.order_by(TestRun.started_at.desc()).all()
    return jsonify(
        [
            {
                "id": r.id,
                "agent_name": r.agent_name,
                "course_id": r.course_id,
                "status": r.status,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "submission_count": r.get_submission_count(),
            }
            for r in runs
        ]
    )
