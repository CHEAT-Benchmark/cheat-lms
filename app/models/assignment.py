import json
from app import db


class Assignment(db.Model):
    __tablename__ = "assignments"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    assignment_type = db.Column(db.String(20), nullable=False)  # quiz, essay, discussion
    description = db.Column(db.Text)
    points = db.Column(db.Integer, default=100)
    time_limit_minutes = db.Column(db.Integer)  # For quizzes
    min_words = db.Column(db.Integer)  # For essays/discussions
    max_words = db.Column(db.Integer)  # For essays
    replies_required = db.Column(db.Integer)  # For discussions
    rubric_json = db.Column(db.Text)  # JSON rubric for essays
    due_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    source_file = db.Column(db.String(500))  # Path to original plain text file

    course = db.relationship("Course", back_populates="assignments")
    questions = db.relationship("Question", back_populates="assignment", lazy="dynamic", order_by="Question.order")
    submissions = db.relationship("Submission", back_populates="assignment", lazy="dynamic")
    discussion_posts = db.relationship("DiscussionPost", back_populates="assignment", lazy="dynamic")

    @property
    def rubric(self):
        if self.rubric_json:
            return json.loads(self.rubric_json)
        return None

    @rubric.setter
    def rubric(self, value):
        self.rubric_json = json.dumps(value) if value else None

    def __repr__(self):
        return f"<Assignment {self.title}>"


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)  # multiple-choice, true-false, short-answer, fill-blank
    text = db.Column(db.Text, nullable=False)
    points = db.Column(db.Integer, default=10)
    choices_json = db.Column(db.Text)  # JSON array of choices for MC/TF
    correct_answer = db.Column(db.Text)  # Correct answer(s)

    assignment = db.relationship("Assignment", back_populates="questions")
    answers = db.relationship("Answer", back_populates="question", lazy="dynamic")

    @property
    def choices(self):
        if self.choices_json:
            return json.loads(self.choices_json)
        return None

    @choices.setter
    def choices(self, value):
        self.choices_json = json.dumps(value) if value else None

    def __repr__(self):
        return f"<Question {self.id} ({self.question_type})>"
