from datetime import datetime
from flask import Blueprint, render_template, abort, request, session
from flask_login import login_required, current_user

from app.models.course import Enrollment
from app.models.assignment import Assignment
from app.models.submission import Submission, DiscussionPost

assignments_bp = Blueprint("assignments", __name__)


@assignments_bp.route("/assignment/<int:assignment_id>")
@login_required
def view_assignment(assignment_id):
    """View an assignment (redirects to appropriate type view)."""
    assignment = Assignment.query.get_or_404(assignment_id)

    # Check enrollment
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id, course_id=assignment.course_id
    ).first()

    if not enrollment:
        abort(403)

    if assignment.assignment_type == "quiz":
        return render_quiz(assignment)
    elif assignment.assignment_type == "essay":
        return render_essay(assignment)
    elif assignment.assignment_type == "discussion":
        return render_discussion(assignment)

    abort(400)


def render_quiz(assignment):
    """Render quiz view."""
    # Check for existing submission
    submission = Submission.query.filter_by(
        assignment_id=assignment.id, user_id=current_user.id
    ).first()

    # Track when quiz was first viewed (for timing)
    if not submission:
        session_key = f"quiz_started_{assignment.id}"
        if session_key not in session:
            session[session_key] = datetime.utcnow().isoformat()

    questions = assignment.questions.order_by("order").all()

    return render_template(
        "quiz.html",
        assignment=assignment,
        questions=questions,
        submission=submission,
    )


def render_essay(assignment):
    """Render essay view."""
    # Check for existing submission
    submission = Submission.query.filter_by(
        assignment_id=assignment.id, user_id=current_user.id
    ).first()

    return render_template(
        "essay.html",
        assignment=assignment,
        submission=submission,
    )


def render_discussion(assignment):
    """Render discussion view."""
    # Get all posts for this discussion
    posts = DiscussionPost.query.filter_by(
        assignment_id=assignment.id, parent_id=None
    ).order_by(DiscussionPost.posted_at.desc()).all()

    # Check if user has posted
    user_post = DiscussionPost.query.filter_by(
        assignment_id=assignment.id,
        user_id=current_user.id,
        parent_id=None,
    ).first()

    # Count user's replies
    user_replies_count = DiscussionPost.query.filter(
        DiscussionPost.assignment_id == assignment.id,
        DiscussionPost.user_id == current_user.id,
        DiscussionPost.parent_id.isnot(None),
    ).count()

    return render_template(
        "discussion.html",
        assignment=assignment,
        posts=posts,
        user_post=user_post,
        user_replies_count=user_replies_count,
    )
