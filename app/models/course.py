from app import db


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    term = db.Column(db.String(50), default="Fall 2024")
    instructor_name = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    enrollments = db.relationship("Enrollment", back_populates="course", lazy="dynamic")
    assignments = db.relationship("Assignment", back_populates="course", lazy="dynamic")

    def __repr__(self):
        return f"<Course {self.code}>"


class Enrollment(db.Model):
    __tablename__ = "enrollments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    role = db.Column(db.String(20), default="student")  # student, ta, instructor
    enrolled_at = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship("User", back_populates="enrollments")
    course = db.relationship("Course", back_populates="enrollments")

    __table_args__ = (db.UniqueConstraint("user_id", "course_id"),)
