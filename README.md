# CHEAT LMS

A high-fidelity simulated LMS for AI academic integrity research. Part of the [CHEAT Benchmark](https://github.com/CHEAT-Benchmark) project.

## Overview

CHEAT LMS is a "honeypot" server that mimics core learning management system functions while capturing deep telemetry. It supports three assignment types - quizzes, essays, and discussions - and tracks everything from HTTP requests to client-side behavioral events like mouse movements and keystroke timing.

This simulated LMS serves as one component of the CHEAT Benchmark, which quantifies AI models' complicity in academic dishonesty.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
python run.py
```

The app runs at http://127.0.0.1:5000

### Demo Accounts

Three student accounts are available (password: `student123`):
- jsmith
- emartinez
- twang

## Usage

```bash
# Standard startup
python run.py

# Reset database and reload courses from assessment files
python run.py --reload

# Enable Flask debug mode
python run.py --debug

# View telemetry
python run.py --telemetry                    # Last 50 entries
python run.py --telemetry-user USERNAME      # Filter by user
python run.py --telemetry-limit 100          # Last N entries
python run.py --telemetry-format json        # Output as JSON
python run.py --telemetry-clear              # Delete all telemetry
```

## Running Tests

```bash
pytest                           # Run all tests
pytest tests/test_app.py         # Run specific test file
pytest tests/test_app.py::test_login  # Run single test
```

## Contributing

### Submit via GitHub Issues (Recommended)

The easiest way to contribute is through our submission forms. Go to the [Issues page](https://github.com/CHEAT-Benchmark/cheat-lms/issues) and click the green **New Issue** button at the top right of the screen. You'll see options to submit:

- **Quiz** — Multiple-choice and true/false questions
- **Essay Assignment** — Essay prompts with rubrics
- **Discussion Assignment** — Discussion topics with grading criteria
- **Adversarial Prompt** — Prompts that trick AI models into completing academic work

Fill out the form and submit. A maintainer will review your contribution and add it to the repository.

All submissions are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

### Assessment File Format

Assessments are plain-text files stored in `assessments/courses/`. Each course has its own folder containing a `course.txt` metadata file and assignment files.

See the formatting guides for each assessment type:
- [Quiz Format](assessments/formatting-quiz.md)
- [Essay Format](assessments/formatting-essay.md)
- [Discussion Format](assessments/formatting-discussion.md)

### Adding a New Course (For Developers)

1. Create a folder under `assessments/courses/` (e.g., `assessments/courses/bio200/`)
2. Add a `course.txt` file with course metadata:
   ```
   CODE: BIO200
   NAME: Introduction to Biology
   DESCRIPTION: Fundamentals of biological science.
   TERM: Fall 2024
   INSTRUCTOR: Dr. Jane Smith
   ```
3. Add assignment files (e.g., `quiz1.txt`, `essay1.txt`)
4. Restart the server with `--reload` to load the new course

## Architecture

CHEAT LMS is a Flask application with SQLite storage.

```
app/
├── routes/          # Flask blueprints (auth, courses, assignments, submissions, telemetry_api)
├── models/          # SQLAlchemy models (User, Course, Assignment, Submission, etc.)
├── parsers/         # Plain-text assessment file parsers
├── telemetry/       # Request logging middleware and storage
├── templates/       # Jinja2 HTML templates
└── static/          # CSS and client-side JavaScript

assessments/
└── courses/         # Course and assignment definitions

data/                # Runtime data (database, telemetry logs)
```

### Telemetry System

Two telemetry streams capture user behavior:

1. **Request telemetry** — Logs all HTTP requests to `data/telemetry.jsonl`
2. **Behavioral telemetry** — Client-side events (clicks, scrolls, question timing) stored in `data/behavioral_telemetry.jsonl`

## License

cheat-lms is licensed under the MIT license.
