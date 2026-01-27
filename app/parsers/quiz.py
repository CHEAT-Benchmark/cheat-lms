import re
from dataclasses import dataclass, field


@dataclass
class QuizQuestion:
    number: int
    points: int
    question_type: str
    text: str
    choices: list = field(default_factory=list)
    correct_answer: str = None


@dataclass
class QuizData:
    title: str
    time_limit_minutes: int = None
    points: int = 100
    questions: list = field(default_factory=list)


def parse_quiz(content: str) -> QuizData:
    """Parse plain text quiz format into structured data."""
    lines = content.strip().split("\n")

    # Parse header
    header = {}
    body_start = 0

    for i, line in enumerate(lines):
        line = line.strip()
        if line == "---":
            body_start = i + 1
            break
        if ":" in line:
            key, value = line.split(":", 1)
            header[key.strip().upper()] = value.strip()

    quiz = QuizData(
        title=header.get("TITLE", "Untitled Quiz"),
        time_limit_minutes=parse_time_limit(header.get("TIME_LIMIT")),
        points=int(header.get("POINTS", 100)),
    )

    # Parse questions
    body = "\n".join(lines[body_start:])
    question_blocks = re.split(r"\n\s*\n+", body.strip())

    for block in question_blocks:
        if not block.strip():
            continue
        question = parse_question(block.strip())
        if question:
            quiz.questions.append(question)

    return quiz


def parse_time_limit(value: str) -> int:
    """Parse time limit string like '30 minutes' into integer minutes."""
    if not value:
        return None
    match = re.search(r"(\d+)", value)
    if match:
        return int(match.group(1))
    return None


def parse_question(block: str) -> QuizQuestion:
    """Parse a single question block."""
    lines = block.strip().split("\n")
    if not lines:
        return None

    # Parse question header: Q1 [10 points] (multiple-choice)
    header_match = re.match(
        r"Q(\d+)\s*\[(\d+)\s*points?\]\s*\(([^)]+)\)",
        lines[0].strip(),
        re.IGNORECASE,
    )

    if not header_match:
        return None

    number = int(header_match.group(1))
    points = int(header_match.group(2))
    question_type = header_match.group(3).lower().strip()

    # Only support multiple-choice and true-false (auto-gradable types)
    if question_type not in ["multiple-choice", "true-false"]:
        return None

    # Get question text (everything after header until choices start)
    remaining_lines = lines[1:]
    text_lines = []
    choice_lines = []
    in_choices = False

    for line in remaining_lines:
        stripped = line.strip()
        # Check if this is a choice line (A), B), etc. or True/False)
        if re.match(r"^[A-E]\)|^\*?\s*(True|False)$", stripped, re.IGNORECASE):
            in_choices = True
        if in_choices:
            choice_lines.append(stripped)
        else:
            text_lines.append(stripped)

    text = " ".join(text_lines).strip()
    choices = []
    correct_answer = None

    if question_type in ["multiple-choice", "true-false"]:
        for choice_line in choice_lines:
            is_correct = choice_line.startswith("*") or choice_line.endswith("*")
            choice_clean = choice_line.replace("*", "").strip()

            if question_type == "true-false":
                choices.append({"label": choice_clean, "text": choice_clean})
                if is_correct:
                    correct_answer = choice_clean
            else:
                # Parse A) Answer text
                choice_match = re.match(r"([A-E])\)\s*(.+)", choice_clean)
                if choice_match:
                    label = choice_match.group(1)
                    choice_text = choice_match.group(2).strip()
                    choices.append({"label": label, "text": choice_text})
                    if is_correct:
                        correct_answer = label

    return QuizQuestion(
        number=number,
        points=points,
        question_type=question_type,
        text=text,
        choices=choices,
        correct_answer=correct_answer,
    )
