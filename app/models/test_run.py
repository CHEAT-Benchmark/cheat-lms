from datetime import datetime
from app import db


class TestRun(db.Model):
    """A test run that evaluates an AI agent against a course's assignments."""

    __tablename__ = "test_runs"

    id = db.Column(db.Integer, primary_key=True)
    agent_name = db.Column(db.String(100), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    prompts = db.Column(db.JSON, nullable=False)  # List of prompt filenames
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="running")  # running, completed

    # Current position in the test matrix
    current_prompt_index = db.Column(db.Integer, default=0)
    current_assignment_index = db.Column(db.Integer, default=0)

    course = db.relationship("Course", backref="test_runs")
    results = db.relationship(
        "TestRunResult", backref="test_run", cascade="all, delete-orphan"
    )

    def get_submission_count(self):
        """Count how many assignments were submitted during this test run."""
        from app.models.submission import Submission

        if not self.started_at:
            return 0

        query = Submission.query.filter(
            Submission.submitted_at >= self.started_at,
        )
        if self.completed_at:
            query = query.filter(Submission.submitted_at <= self.completed_at)

        # Filter to assignments in this course
        from app.models.assignment import Assignment

        course_assignment_ids = [
            a.id for a in Assignment.query.filter_by(course_id=self.course_id).all()
        ]
        query = query.filter(Submission.assignment_id.in_(course_assignment_ids))

        return query.count()


class TestRunResult(db.Model):
    """Result of testing a specific prompt against a specific assignment."""

    __tablename__ = "test_run_results"

    id = db.Column(db.Integer, primary_key=True)
    test_run_id = db.Column(
        db.Integer, db.ForeignKey("test_runs.id"), nullable=False
    )
    prompt_file = db.Column(db.String(100), nullable=False)
    assignment_id = db.Column(
        db.Integer, db.ForeignKey("assignments.id"), nullable=False
    )
    submitted = db.Column(db.Boolean, default=False)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    assignment = db.relationship("Assignment")
