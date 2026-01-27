import re
from dataclasses import dataclass, field


@dataclass
class RubricItem:
    name: str
    percentage: int
    description: str


@dataclass
class EssayData:
    title: str
    min_words: int = None
    max_words: int = None
    prompt: str = ""
    rubric: list = field(default_factory=list)


def parse_essay(content: str) -> EssayData:
    """Parse plain text essay format into structured data."""
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

    essay = EssayData(
        title=header.get("TITLE", "Untitled Essay"),
        min_words=int(header.get("MIN_WORDS", 0)) or None,
        max_words=int(header.get("MAX_WORDS", 0)) or None,
    )

    # Parse body sections
    body = "\n".join(lines[body_start:])

    # Extract prompt
    prompt_match = re.search(r"PROMPT:\s*\n(.*?)(?=\n\s*RUBRIC:|$)", body, re.DOTALL | re.IGNORECASE)
    if prompt_match:
        essay.prompt = prompt_match.group(1).strip()

    # Extract rubric
    rubric_match = re.search(r"RUBRIC:\s*\n(.*?)$", body, re.DOTALL | re.IGNORECASE)
    if rubric_match:
        rubric_text = rubric_match.group(1).strip()
        essay.rubric = parse_rubric(rubric_text)

    return essay


def parse_rubric(text: str) -> list:
    """Parse rubric items from text."""
    rubric = []
    lines = text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line or not line.startswith("-"):
            continue

        line = line[1:].strip()  # Remove leading dash

        # Parse: Thesis (20%): Clear, arguable thesis statement
        match = re.match(r"([^(]+)\s*\((\d+)%\):\s*(.+)", line)
        if match:
            rubric.append(RubricItem(
                name=match.group(1).strip(),
                percentage=int(match.group(2)),
                description=match.group(3).strip(),
            ))

    return rubric
