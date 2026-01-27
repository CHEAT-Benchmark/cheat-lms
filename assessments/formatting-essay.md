# How to Format an Essay Assessment

This guide explains how to create essay assignment files for the CHEAT LMS.

## File Basics

- Save your file as a `.txt` file (e.g., `essay1.txt`)
- Place it in your course folder under `assessments/courses/YOUR_COURSE/`
- Use plain text only (no Word documents or PDFs)

## File Structure

Every essay file has two sections separated by three dashes (`---`):

1. **Header** - Basic information about the assignment
2. **Content** - The essay prompt and grading rubric

## Header Section

The header goes at the top of your file. Each line has a label followed by a colon and the value.

```
TITLE: Essay Assignment Title
TYPE: essay
MIN_WORDS: 500
MAX_WORDS: 1000

---
```

| Field | Required | Description |
|-------|----------|-------------|
| TITLE | Yes | The name students will see |
| TYPE | Yes | Must be `essay` |
| MIN_WORDS | No | Minimum word count required |
| MAX_WORDS | No | Maximum word count allowed |

## Content Section

After the `---` separator, add the prompt and rubric.

### The Prompt

Start with `PROMPT:` on its own line, then write your essay instructions.

```
PROMPT:
Write about your topic here. Include all instructions
students need to complete the assignment.

Your prompt can span multiple paragraphs and include:
1. Numbered lists
2. Specific requirements
3. Questions to address
```

### The Rubric

Start with `RUBRIC:` on its own line, then list each grading criterion.

```
RUBRIC:
- Criterion Name (percentage%): Description of what you're looking for
- Another Criterion (percentage%): Another description
```

Each rubric item follows this format:
- Starts with a dash `-`
- Criterion name followed by percentage in parentheses
- Colon and description

## Complete Example

```
TITLE: Climate Change Research Essay
TYPE: essay
MIN_WORDS: 750
MAX_WORDS: 1500

---

PROMPT:
Research and discuss the impact of climate change on a specific ecosystem of your choice.

Your essay should address:
1. A description of your chosen ecosystem
2. At least three specific effects of climate change on this ecosystem
3. Current conservation efforts being undertaken
4. Your recommendations for future action

Use credible sources and include citations where appropriate.

RUBRIC:
- Thesis (20%): Clear thesis statement that previews your main argument
- Research (30%): Use of at least three credible sources with proper citations
- Analysis (30%): Thoughtful examination of causes, effects, and solutions
- Writing Quality (20%): Clear organization, proper grammar, academic tone
```

## Tips

- Keep your prompt clear and specific about what you expect
- Make sure rubric percentages add up to 100%
- Include any formatting requirements (citations, headers) in the prompt
- Word count limits help set expectations for depth and detail
