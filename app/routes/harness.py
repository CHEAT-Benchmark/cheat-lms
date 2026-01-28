import os
from datetime import datetime
from pathlib import Path

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

from app import db
from app.config import BASE_DIR
from app.models.course import Course
from app.models.assignment import Assignment
from app.models.test_run import TestRun, TestRunResult
from app.telemetry.storage import read_telemetry, read_behavioral_telemetry

harness_bp = Blueprint("harness", __name__, url_prefix="/harness")

PROMPTS_DIR = BASE_DIR / "prompts"

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
    return render_template(
        "harness/setup.html",
        agents=AVAILABLE_AGENTS,
        courses=courses,
        prompts=prompts,
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

    # Create test run
    test_run = TestRun(
        agent_name=agent_name,
        course_id=int(course_id),
        prompts=selected_prompts,
        status="running",
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

    # Record result for current combination
    submitted = request.form.get("submitted") == "yes"

    if (
        test_run.current_prompt_index < len(test_run.prompts)
        and test_run.current_assignment_index < len(assignments)
    ):
        result = TestRunResult(
            test_run_id=test_run.id,
            prompt_file=test_run.prompts[test_run.current_prompt_index],
            assignment_id=assignments[test_run.current_assignment_index].id,
            submitted=submitted,
            started_at=test_run.started_at,
            completed_at=datetime.utcnow(),
        )
        db.session.add(result)

    # Advance to next combination
    test_run.current_assignment_index += 1
    if test_run.current_assignment_index >= len(assignments):
        test_run.current_assignment_index = 0
        test_run.current_prompt_index += 1

    # Check if we've completed all combinations
    if test_run.current_prompt_index >= len(test_run.prompts):
        test_run.status = "completed"
        test_run.completed_at = datetime.utcnow()

    db.session.commit()

    if test_run.status == "completed":
        return redirect(url_for("harness.results", run_id=run_id))

    return redirect(url_for("harness.run", run_id=run_id))


@harness_bp.route("/run/<int:run_id>/complete", methods=["POST"])
def complete_run(run_id):
    """Mark the test run as complete and go to results."""
    test_run = TestRun.query.get_or_404(run_id)
    test_run.status = "completed"
    test_run.completed_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for("harness.results", run_id=run_id))


@harness_bp.route("/results/<int:run_id>")
def results(run_id):
    """Results dashboard showing submission counts, grid, and timeline."""
    test_run = TestRun.query.get_or_404(run_id)
    assignments = Assignment.query.filter_by(course_id=test_run.course_id).all()

    # Build results grid
    grid = {}
    for result in test_run.results:
        key = (result.prompt_file, result.assignment_id)
        grid[key] = result

    # Get submission count
    submission_count = test_run.get_submission_count()

    # Get telemetry for timeline
    start_ts = test_run.started_at.timestamp() if test_run.started_at else 0
    end_ts = (
        test_run.completed_at.timestamp()
        if test_run.completed_at
        else datetime.utcnow().timestamp()
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
        grid=grid,
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
