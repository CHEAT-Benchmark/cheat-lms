# How to Format a Discussion Assessment

This guide explains how to create discussion assignment files for the CHEAT LMS.

## File Basics

- Save your file as a `.txt` file (e.g., `discussion1.txt`)
- Place it in your course folder under `assessments/courses/YOUR_COURSE/`
- Use plain text only (no Word documents or PDFs)

## File Structure

Every discussion file has two sections separated by three dashes (`---`):

1. **Header** - Basic information about the discussion
2. **Content** - The discussion prompt and grading criteria

## Header Section

The header goes at the top of your file. Each line has a label followed by a colon and the value.

```
TITLE: Week 1 Discussion - Topic Name
TYPE: discussion
MIN_WORDS: 250
REPLIES_REQUIRED: 2

---
```

| Field | Required | Description |
|-------|----------|-------------|
| TITLE | Yes | The name students will see |
| TYPE | Yes | Must be `discussion` |
| MIN_WORDS | No | Minimum word count for the initial post |
| REPLIES_REQUIRED | No | Number of replies to classmates required |

## Content Section

After the `---` separator, add the prompt and grading criteria.

### The Prompt

Start with `PROMPT:` on its own line, then write your discussion topic and questions.

```
PROMPT:
Introduce your discussion topic here. Provide context
that helps students understand the subject.

Consider including:
1. Background information or context
2. Specific questions for students to address
3. Guidelines for engaging with classmates
```

### The Grading Criteria

Start with `GRADING:` on its own line, then list how the discussion will be evaluated.

```
GRADING:
- Initial Post (percentage%): Description of expectations
- Replies (percentage%): Description of reply expectations
```

Each grading item follows this format:
- Starts with a dash `-`
- Criterion name followed by percentage in parentheses
- Colon and description

## Complete Example

```
TITLE: Week 5 Discussion - Social Media and Society
TYPE: discussion
MIN_WORDS: 200
REPLIES_REQUIRED: 2

---

PROMPT:
Social media has transformed how we communicate, consume news, and form communities. For this discussion, reflect on the role of social media in modern society.

Address the following questions in your initial post:
1. What do you see as the primary benefits of social media for society?
2. What are the most significant risks or drawbacks?
3. How has social media affected your own life, positively or negatively?

When replying to classmates, engage thoughtfully with their perspectives. You might share whether you agree or disagree and why, ask follow-up questions, or offer additional examples that support or challenge their points.

GRADING:
- Initial Post (60%): Well-developed response that addresses all three questions with specific examples
- Replies (40%): Substantive replies to at least two classmates that advance the conversation
```

## Tips

- Pose open-ended questions that encourage diverse perspectives
- Be clear about expectations for both initial posts and replies
- The `REPLIES_REQUIRED` field tells students how many peer responses they need
- Consider including guidance on what makes a good reply (not just "I agree")
- Grading percentages should add up to 100%
