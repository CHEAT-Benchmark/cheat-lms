# How to Format a Quiz Assessment

This guide explains how to create quiz files for the CHEAT LMS.

## File Basics

- Save your file as a `.txt` file (e.g., `quiz1.txt`)
- Place it in your course folder under `assessments/courses/YOUR_COURSE/`
- Use plain text only (no Word documents or PDFs)

## File Structure

Every quiz file has two sections separated by three dashes (`---`):

1. **Header** - Basic information about the quiz
2. **Questions** - The quiz questions and answers

## Header Section

The header goes at the top of your file. Each line has a label followed by a colon and the value.

```
TITLE: Your Quiz Title Here
TYPE: quiz
TIME_LIMIT: 30 minutes
POINTS: 100

---
```

| Field | Required | Description |
|-------|----------|-------------|
| TITLE | Yes | The name students will see |
| TYPE | Yes | Must be `quiz` |
| TIME_LIMIT | No | How long students have (e.g., `30 minutes`) |
| POINTS | No | Total points for the quiz |

## Question Formats

After the `---` separator, add your questions. The system supports two question types.

### Multiple Choice Questions

```
Q1 [10 points] (multiple-choice)
What is the capital of France?
A) London
B) Paris *
C) Berlin
D) Madrid
```

- Start with `Q` followed by the question number
- Put the point value in square brackets: `[10 points]`
- Put the question type in parentheses: `(multiple-choice)`
- List each answer choice on its own line starting with `A)`, `B)`, `C)`, `D)`
- Mark the correct answer with an asterisk `*` at the end of the line

### True/False Questions

```
Q2 [10 points] (true-false)
The Earth is the third planet from the Sun.
* True
False
```

- Same header format as multiple choice
- Write the statement on the line after the header
- List `True` and `False` on separate lines
- Put an asterisk `*` before the correct answer

## Complete Example

```
TITLE: Geography Quiz 1
TYPE: quiz
TIME_LIMIT: 20 minutes
POINTS: 30

---

Q1 [10 points] (multiple-choice)
What is the largest ocean on Earth?
A) Atlantic Ocean
B) Indian Ocean
C) Pacific Ocean *
D) Arctic Ocean

Q2 [10 points] (true-false)
Mount Everest is located in the Himalayas.
* True
False

Q3 [10 points] (multiple-choice)
Which continent has the most countries?
A) Asia
B) Africa *
C) Europe
D) South America
```

## Tips

- Leave a blank line between questions for readability
- Question numbers should be sequential (Q1, Q2, Q3...)
- Double-check that exactly one answer is marked correct for each question
- The asterisk `*` must be on the same line as the correct answer
