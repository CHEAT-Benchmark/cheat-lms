import re
from dataclasses import dataclass, field


@dataclass
class GradingItem:
    name: str
    percentage: int
    description: str


@dataclass
class DiscussionData:
    title: str
    min_words: int = 250
    replies_required: int = 2
    prompt: str = ""
    grading: list = field(default_factory=list)


def parse_discussion(content: str) -> DiscussionData:
    """Parse plain text discussion format into structured data."""
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

    discussion = DiscussionData(
        title=header.get("TITLE", "Untitled Discussion"),
        min_words=int(header.get("MIN_WORDS", 250)),
        replies_required=int(header.get("REPLIES_REQUIRED", 2)),
    )

    # Parse body sections
    body = "\n".join(lines[body_start:])

    # Extract prompt
    prompt_match = re.search(r"PROMPT:\s*\n(.*?)(?=\n\s*GRADING:|$)", body, re.DOTALL | re.IGNORECASE)
    if prompt_match:
        discussion.prompt = prompt_match.group(1).strip()

    # Extract grading criteria
    grading_match = re.search(r"GRADING:\s*\n(.*?)$", body, re.DOTALL | re.IGNORECASE)
    if grading_match:
        grading_text = grading_match.group(1).strip()
        discussion.grading = parse_grading(grading_text)

    return discussion


def parse_grading(text: str) -> list:
    """Parse grading items from text."""
    grading = []
    lines = text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line or not line.startswith("-"):
            continue

        line = line[1:].strip()  # Remove leading dash

        # Parse: Initial post (60%): Thoughtful, well-supported argument
        match = re.match(r"([^(]+)\s*\((\d+)%\):\s*(.+)", line)
        if match:
            grading.append(GradingItem(
                name=match.group(1).strip(),
                percentage=int(match.group(2)),
                description=match.group(3).strip(),
            ))

    return grading
