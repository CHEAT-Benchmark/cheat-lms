import os
from pathlib import Path

from app import db
from app.config import ASSESSMENTS_DIR
from app.models.course import Course
from app.models.assignment import Assignment, Question
from app.parsers.quiz import parse_quiz
from app.parsers.essay import parse_essay
from app.parsers.discussion import parse_discussion


def load_all_courses():
    """Load all courses from the assessments directory."""
    courses_dir = ASSESSMENTS_DIR / "courses"
    if not courses_dir.exists():
        return

    for course_dir in courses_dir.iterdir():
        if course_dir.is_dir():
            load_course(course_dir)


def load_course(course_dir: Path):
    """Load a single course from its directory."""
    course_file = course_dir / "course.txt"

    # Parse course metadata
    course_data = {"code": course_dir.name.upper(), "name": course_dir.name}
    if course_file.exists():
        course_data = parse_course_file(course_file)
        course_data.setdefault("code", course_dir.name.upper())

    # Check if course already exists
    existing = Course.query.filter_by(code=course_data["code"]).first()
    if existing:
        course = existing
    else:
        course = Course(
            code=course_data["code"],
            name=course_data.get("name", course_data["code"]),
            description=course_data.get("description", ""),
            term=course_data.get("term", "Fall 2024"),
            instructor_name=course_data.get("instructor", ""),
        )
        db.session.add(course)
        db.session.commit()

    # Load assignments
    for file_path in course_dir.iterdir():
        if file_path.suffix == ".txt" and file_path.name != "course.txt":
            load_assignment(course, file_path)


def parse_course_file(file_path: Path) -> dict:
    """Parse course metadata from course.txt."""
    data = {}
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                data[key.strip().lower()] = value.strip()
    return data


def load_assignment(course: Course, file_path: Path):
    """Load an assignment from a plain text file."""
    with open(file_path, "r") as f:
        content = f.read()

    # Determine type from content
    lines = content.strip().split("\n")
    header = {}
    for line in lines:
        line = line.strip()
        if line == "---":
            break
        if ":" in line:
            key, value = line.split(":", 1)
            header[key.strip().upper()] = value.strip()

    assignment_type = header.get("TYPE", "").lower()
    title = header.get("TITLE", file_path.stem)

    # Check if assignment already exists
    existing = Assignment.query.filter_by(
        course_id=course.id, title=title
    ).first()
    if existing:
        return existing

    if assignment_type == "quiz":
        return load_quiz(course, file_path, content)
    elif assignment_type == "essay":
        return load_essay(course, file_path, content)
    elif assignment_type == "discussion":
        return load_discussion(course, file_path, content)


def load_quiz(course: Course, file_path: Path, content: str):
    """Load a quiz assignment."""
    quiz_data = parse_quiz(content)

    assignment = Assignment(
        course_id=course.id,
        title=quiz_data.title,
        assignment_type="quiz",
        points=quiz_data.points,
        time_limit_minutes=quiz_data.time_limit_minutes,
        source_file=str(file_path),
    )
    db.session.add(assignment)
    db.session.commit()

    # Add questions
    for q in quiz_data.questions:
        question = Question(
            assignment_id=assignment.id,
            order=q.number,
            question_type=q.question_type,
            text=q.text,
            points=q.points,
            correct_answer=q.correct_answer,
        )
        question.choices = q.choices
        db.session.add(question)

    db.session.commit()
    return assignment


def load_essay(course: Course, file_path: Path, content: str):
    """Load an essay assignment."""
    essay_data = parse_essay(content)

    rubric_list = [
        {"name": r.name, "percentage": r.percentage, "description": r.description}
        for r in essay_data.rubric
    ]

    assignment = Assignment(
        course_id=course.id,
        title=essay_data.title,
        assignment_type="essay",
        description=essay_data.prompt,
        min_words=essay_data.min_words,
        max_words=essay_data.max_words,
        source_file=str(file_path),
    )
    assignment.rubric = rubric_list
    db.session.add(assignment)
    db.session.commit()
    return assignment


def load_discussion(course: Course, file_path: Path, content: str):
    """Load a discussion assignment."""
    discussion_data = parse_discussion(content)

    grading_list = [
        {"name": g.name, "percentage": g.percentage, "description": g.description}
        for g in discussion_data.grading
    ]

    assignment = Assignment(
        course_id=course.id,
        title=discussion_data.title,
        assignment_type="discussion",
        description=discussion_data.prompt,
        min_words=discussion_data.min_words,
        replies_required=discussion_data.replies_required,
        source_file=str(file_path),
    )
    assignment.rubric = grading_list
    db.session.add(assignment)
    db.session.commit()
    return assignment
