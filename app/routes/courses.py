from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user

from app.models.course import Course, Enrollment
from app.models.assignment import Assignment
from app.models.submission import Submission, DiscussionPost

courses_bp = Blueprint("courses", __name__)


@courses_bp.route("/dashboard")
@login_required
def dashboard():
    """Show all enrolled courses."""
    enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
    courses = [e.course for e in enrollments]
    return render_template("dashboard.html", courses=courses)


@courses_bp.route("/course/<int:course_id>")
@login_required
def course_view(course_id):
    """Show a single course with its assignments."""
    # Check enrollment
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id, course_id=course_id
    ).first()

    if not enrollment:
        abort(403)

    course = Course.query.get_or_404(course_id)
    assignments = Assignment.query.filter_by(course_id=course_id).order_by(
        Assignment.created_at
    ).all()

    # Get submission status for each assignment
    assignment_status = {}
    for assignment in assignments:
        if assignment.assignment_type == "discussion":
            # Check if user has posted
            post = DiscussionPost.query.filter_by(
                assignment_id=assignment.id,
                user_id=current_user.id,
                parent_id=None,
            ).first()
            assignment_status[assignment.id] = "submitted" if post else "not_started"
        else:
            submission = Submission.query.filter_by(
                assignment_id=assignment.id, user_id=current_user.id
            ).first()
            assignment_status[assignment.id] = "submitted" if submission else "not_started"

    return render_template(
        "course.html",
        course=course,
        assignments=assignments,
        assignment_status=assignment_status,
    )
