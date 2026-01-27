import json
from datetime import datetime
from flask import Blueprint, request, redirect, url_for, flash, abort, session
from flask_login import login_required, current_user

from app import db
from app.models.course import Enrollment
from app.models.assignment import Assignment, Question
from app.models.submission import Submission, Answer, DiscussionPost

submissions_bp = Blueprint("submissions", __name__)


@submissions_bp.route("/submit/quiz/<int:assignment_id>", methods=["POST"])
@login_required
def submit_quiz(assignment_id):
    """Submit quiz answers."""
    assignment = Assignment.query.get_or_404(assignment_id)

    # Check enrollment
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id, course_id=assignment.course_id
    ).first()
    if not enrollment:
        abort(403)

    # Check for existing submission
    existing = Submission.query.filter_by(
        assignment_id=assignment_id, user_id=current_user.id
    ).first()
    if existing:
        flash("You have already submitted this quiz.", "warning")
        return redirect(url_for("assignments.view_assignment", assignment_id=assignment_id))

    # Parse question timing data from hidden field
    question_timings = {}
    timings_json = request.form.get("question_timings", "{}")
    try:
        question_timings = json.loads(timings_json)
    except json.JSONDecodeError:
        pass

    # Get quiz start time from session
    session_key = f"quiz_started_{assignment_id}"
    started_at = session.get(session_key)
    if started_at:
        started_at = datetime.fromisoformat(started_at)
        # Clear from session
        session.pop(session_key, None)

    # Calculate time spent
    time_spent_seconds = None
    if started_at:
        time_spent_seconds = int((datetime.utcnow() - started_at).total_seconds())

    # Create submission
    submission = Submission(
        user_id=current_user.id,
        assignment_id=assignment_id,
        user_agent=request.headers.get("User-Agent", ""),
        ip_address=request.remote_addr,
        started_at=started_at,
        time_spent_seconds=time_spent_seconds,
    )
    db.session.add(submission)
    db.session.commit()

    # Process answers
    total_score = 0
    questions = Question.query.filter_by(assignment_id=assignment_id).all()

    for question in questions:
        answer_key = f"question_{question.id}"
        answer_text = request.form.get(answer_key, "")

        # Check correctness (only multiple-choice and true-false supported)
        is_correct = answer_text == question.correct_answer
        points_earned = question.points if is_correct else 0
        total_score += points_earned

        # Get time to answer from timing data
        time_to_answer_ms = None
        q_timing = question_timings.get(str(question.id))
        if q_timing and q_timing.get("answeredAt") and q_timing.get("focusedAt"):
            time_to_answer_ms = q_timing["answeredAt"] - q_timing["focusedAt"]

        answer = Answer(
            submission_id=submission.id,
            question_id=question.id,
            answer_text=answer_text,
            is_correct=is_correct,
            points_earned=points_earned,
            time_to_answer_ms=time_to_answer_ms,
        )
        db.session.add(answer)

    submission.score = total_score
    db.session.commit()

    flash(f"Quiz submitted! Your score: {total_score}/{assignment.points}", "success")
    return redirect(url_for("courses.course_view", course_id=assignment.course_id))


@submissions_bp.route("/submit/essay/<int:assignment_id>", methods=["POST"])
@login_required
def submit_essay(assignment_id):
    """Submit essay."""
    assignment = Assignment.query.get_or_404(assignment_id)

    # Check enrollment
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id, course_id=assignment.course_id
    ).first()
    if not enrollment:
        abort(403)

    # Check for existing submission
    existing = Submission.query.filter_by(
        assignment_id=assignment_id, user_id=current_user.id
    ).first()
    if existing:
        flash("You have already submitted this essay.", "warning")
        return redirect(url_for("assignments.view_assignment", assignment_id=assignment_id))

    content = request.form.get("content", "").strip()

    # Validate word count
    word_count = len(content.split())
    if assignment.min_words and word_count < assignment.min_words:
        flash(f"Essay must be at least {assignment.min_words} words. Current: {word_count}", "error")
        return redirect(url_for("assignments.view_assignment", assignment_id=assignment_id))

    if assignment.max_words and word_count > assignment.max_words:
        flash(f"Essay must be at most {assignment.max_words} words. Current: {word_count}", "error")
        return redirect(url_for("assignments.view_assignment", assignment_id=assignment_id))

    # Create submission
    submission = Submission(
        user_id=current_user.id,
        assignment_id=assignment_id,
        content=content,
        user_agent=request.headers.get("User-Agent", ""),
        ip_address=request.remote_addr,
    )
    db.session.add(submission)
    db.session.commit()

    flash("Essay submitted successfully!", "success")
    return redirect(url_for("courses.course_view", course_id=assignment.course_id))


@submissions_bp.route("/submit/discussion/<int:assignment_id>", methods=["POST"])
@login_required
def submit_discussion(assignment_id):
    """Submit discussion post or reply."""
    assignment = Assignment.query.get_or_404(assignment_id)

    # Check enrollment
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id, course_id=assignment.course_id
    ).first()
    if not enrollment:
        abort(403)

    content = request.form.get("content", "").strip()
    parent_id = request.form.get("parent_id")

    if parent_id:
        parent_id = int(parent_id)
        # Verify parent exists and is for this assignment
        parent = DiscussionPost.query.filter_by(
            id=parent_id, assignment_id=assignment_id
        ).first()
        if not parent:
            abort(400)
    else:
        # Check if user already has an initial post
        existing = DiscussionPost.query.filter_by(
            assignment_id=assignment_id,
            user_id=current_user.id,
            parent_id=None,
        ).first()
        if existing:
            flash("You have already posted to this discussion.", "warning")
            return redirect(url_for("assignments.view_assignment", assignment_id=assignment_id))

    # Validate word count for initial posts
    word_count = len(content.split())
    if not parent_id and assignment.min_words and word_count < assignment.min_words:
        flash(f"Post must be at least {assignment.min_words} words. Current: {word_count}", "error")
        return redirect(url_for("assignments.view_assignment", assignment_id=assignment_id))

    # Create post
    post = DiscussionPost(
        assignment_id=assignment_id,
        user_id=current_user.id,
        parent_id=parent_id,
        content=content,
        word_count=word_count,
        user_agent=request.headers.get("User-Agent", ""),
        ip_address=request.remote_addr,
    )
    db.session.add(post)
    db.session.commit()

    if parent_id:
        flash("Reply posted!", "success")
    else:
        flash("Discussion post submitted!", "success")

    return redirect(url_for("assignments.view_assignment", assignment_id=assignment_id))
