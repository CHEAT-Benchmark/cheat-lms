from app import db


class Submission(db.Model):
    __tablename__ = "submissions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=False)
    content = db.Column(db.Text)  # For essays
    score = db.Column(db.Float)
    submitted_at = db.Column(db.DateTime, server_default=db.func.now())
    started_at = db.Column(db.DateTime)  # When quiz was started
    time_spent_seconds = db.Column(db.Integer)
    user_agent = db.Column(db.String(500))
    ip_address = db.Column(db.String(50))

    user = db.relationship("User", back_populates="submissions")
    assignment = db.relationship("Assignment", back_populates="submissions")
    answers = db.relationship("Answer", back_populates="submission", lazy="dynamic")

    __table_args__ = (db.UniqueConstraint("user_id", "assignment_id"),)

    def __repr__(self):
        return f"<Submission {self.id} by User {self.user_id}>"


class Answer(db.Model):
    __tablename__ = "answers"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("submissions.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    answer_text = db.Column(db.Text)
    is_correct = db.Column(db.Boolean)
    points_earned = db.Column(db.Float)
    time_to_answer_ms = db.Column(db.Integer)  # Time from viewing to answering

    submission = db.relationship("Submission", back_populates="answers")
    question = db.relationship("Question", back_populates="answers")

    def __repr__(self):
        return f"<Answer {self.id}>"


class DiscussionPost(db.Model):
    __tablename__ = "discussion_posts"

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("discussion_posts.id"))
    content = db.Column(db.Text, nullable=False)
    word_count = db.Column(db.Integer)
    posted_at = db.Column(db.DateTime, server_default=db.func.now())
    user_agent = db.Column(db.String(500))
    ip_address = db.Column(db.String(50))

    assignment = db.relationship("Assignment", back_populates="discussion_posts")
    user = db.relationship("User", back_populates="discussion_posts")
    parent = db.relationship("DiscussionPost", remote_side=[id], backref="replies")

    def __repr__(self):
        return f"<DiscussionPost {self.id}>"
