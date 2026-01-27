"""Tests for assessment parsers."""

import pytest
from app.parsers.quiz import parse_quiz
from app.parsers.essay import parse_essay
from app.parsers.discussion import parse_discussion


class TestQuizParser:
    def test_parse_basic_quiz(self):
        content = """
TITLE: Test Quiz
TYPE: quiz
TIME_LIMIT: 30 minutes
POINTS: 100

---

Q1 [10 points] (multiple-choice)
What is 2 + 2?
A) 3
B) 4 *
C) 5
D) 6

Q2 [10 points] (true-false)
The sky is blue.
* True
False
"""
        quiz = parse_quiz(content)

        assert quiz.title == "Test Quiz"
        assert quiz.time_limit_minutes == 30
        assert quiz.points == 100
        assert len(quiz.questions) == 2

        q1 = quiz.questions[0]
        assert q1.number == 1
        assert q1.points == 10
        assert q1.question_type == "multiple-choice"
        assert q1.correct_answer == "B"
        assert len(q1.choices) == 4

        q2 = quiz.questions[1]
        assert q2.question_type == "true-false"
        assert q2.correct_answer == "True"

    def test_short_answer_ignored(self):
        """Short answer questions are skipped (not auto-gradable)."""
        content = """
TITLE: Short Answer Quiz
TYPE: quiz
POINTS: 50

---

Q1 [25 points] (short-answer)
Explain your reasoning.

Q2 [25 points] (multiple-choice)
What is 1 + 1?
A) 1
B) 2 *
C) 3
D) 4
"""
        quiz = parse_quiz(content)

        # Only the multiple-choice question should be parsed
        assert len(quiz.questions) == 1
        assert quiz.questions[0].question_type == "multiple-choice"


class TestEssayParser:
    def test_parse_basic_essay(self):
        content = """
TITLE: Test Essay
TYPE: essay
MIN_WORDS: 500
MAX_WORDS: 1000

---

PROMPT:
Write about something important.
Include details and examples.

RUBRIC:
- Thesis (25%): Clear thesis statement
- Evidence (25%): Supporting evidence
- Analysis (25%): Deep analysis
- Writing (25%): Grammar and style
"""
        essay = parse_essay(content)

        assert essay.title == "Test Essay"
        assert essay.min_words == 500
        assert essay.max_words == 1000
        assert "Write about something important" in essay.prompt
        assert len(essay.rubric) == 4
        assert essay.rubric[0].name == "Thesis"
        assert essay.rubric[0].percentage == 25


class TestDiscussionParser:
    def test_parse_basic_discussion(self):
        content = """
TITLE: Weekly Discussion
TYPE: discussion
MIN_WORDS: 250
REPLIES_REQUIRED: 2

---

PROMPT:
Discuss the topic.
Share your thoughts.

GRADING:
- Initial post (60%): Thoughtful response
- Replies (40%): Engage with peers
"""
        discussion = parse_discussion(content)

        assert discussion.title == "Weekly Discussion"
        assert discussion.min_words == 250
        assert discussion.replies_required == 2
        assert "Discuss the topic" in discussion.prompt
        assert len(discussion.grading) == 2
        assert discussion.grading[0].percentage == 60
