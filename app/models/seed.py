from app import db
from app.models.user import User
from app.models.course import Course, Enrollment
from app.parsers.loader import load_all_courses


FAKE_STUDENTS = [
    {
        "username": "jsmith",
        "email": "jsmith@university.edu",
        "password": "student123",
        "full_name": "Jordan Smith",
        "student_id": "STU001234",
    },
    {
        "username": "emartinez",
        "email": "emartinez@university.edu",
        "password": "student123",
        "full_name": "Elena Martinez",
        "student_id": "STU001235",
    },
    {
        "username": "twang",
        "email": "twang@university.edu",
        "password": "student123",
        "full_name": "Tyler Wang",
        "student_id": "STU001236",
    },
    {
        "username": "akim",
        "email": "akim@university.edu",
        "password": "student123",
        "full_name": "Alex Kim",
        "student_id": "STU001237",
    },
    {
        "username": "sjohnson",
        "email": "sjohnson@university.edu",
        "password": "student123",
        "full_name": "Sarah Johnson",
        "student_id": "STU001238",
    },
]


def seed_database():
    """Seed the database with fake students and load courses from assessment files."""
    # Create fake students if they don't exist
    for student_data in FAKE_STUDENTS:
        existing = User.query.filter_by(username=student_data["username"]).first()
        if not existing:
            user = User(
                username=student_data["username"],
                email=student_data["email"],
                full_name=student_data["full_name"],
                student_id=student_data["student_id"],
            )
            user.set_password(student_data["password"])
            db.session.add(user)

    db.session.commit()

    # Load courses from assessment files
    load_all_courses()

    # Enroll all students in all courses
    students = User.query.filter_by(is_instructor=False).all()
    courses = Course.query.all()

    for student in students:
        for course in courses:
            existing = Enrollment.query.filter_by(
                user_id=student.id, course_id=course.id
            ).first()
            if not existing:
                enrollment = Enrollment(user_id=student.id, course_id=course.id)
                db.session.add(enrollment)

    db.session.commit()
