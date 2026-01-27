# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

The following text from the CHEAT Benchmark website describes this project and its purpose. Always keep it in mind when working on the codebase.

> **Agentic AI Automates Cheating**
>
> Model providers fail to provide guardrails that protect academic integrity. The CHEAT Benchmark holds them accountable.

### How It Works

The CHEAT Benchmark quantifies a model's complicity in academic dishonesty. Patterned after frontier AI benchmarks, CHEAT subjects agents to a multi-layered audit:

1. **Simulated LMS**: A high-fidelity "honeypot" server that mimics core LMS functions while capturing deep telemetry - tracking everything from mouse trajectories to user-agent spoofing.

2. **Assessment Library**: A diverse library of real-world assignments and assessments, including threaded discussions, essays, and quizzes.

3. **Prompt Library**: A collection of adversarial prompts, ranging from direct "Do my homework" requests to sophisticated, "socially engineered" ruses.

4. **Agentic Tool Library**: A continuously updated list of "full self-driving" agentic tools and browsers under evaluation.

5. **Test Harness**: An automated tool that systematically runs every tool and every prompt against every assessment.

6. **Scoring Engine**: A tool that translates raw behavioral telemetry and task outcomes into a standardized integrity metric. By applying a weighted rubric to specific model behaviors - ranging from simple compliance to active deception - the Scoring Engine generates the CHEAT Benchmark score for every agent audited.

### Ways to Contribute

- **Amplify the Audit**: Visibility creates accountability.
- **Expand the Assessment Repository**: Contribute discussion prompts, essay assignments, or quizzes with rubrics.
- **Engineer Adversarial Prompts**: Share prompts that trick models into autonomous task completion.
- **Register Emerging Agentic Tools**: Report new agentic browsers, extensions, or autonomous AI tools.
- **Strengthen the Infrastructure**: Contribute to the Python-based Simulated LMS and Test Harness.
- **Calibrate the Complicity Index**: Help refine how agent behaviors should be weighted in scoring.

## Commands

```bash
# Run the app
python run.py                    # Start server at http://127.0.0.1:5000
python run.py --reload           # Reset database and reload courses from assessment files
python run.py --debug            # Enable Flask debug mode

# Tests
pytest                           # Run all tests (verbose by default)
pytest tests/test_app.py         # Run specific test file
pytest tests/test_app.py::test_login  # Run single test

# Telemetry inspection
python run.py --telemetry                    # Show last 50 entries
python run.py --telemetry-user USERNAME      # Filter by user
python run.py --telemetry-limit 100          # Show last N entries
python run.py --telemetry-format json        # Output as JSON (or jsonl, pretty)
python run.py --telemetry-clear              # Delete all telemetry
```

Demo accounts use password `student123`: jsmith, emartinez, twang

## Architecture

CHEAT LMS is a Flask app simulating Canvas LMS for research purposes. It supports three assignment types (quiz, essay, discussion) with comprehensive telemetry for tracking user behavior.

### Application Flow

1. **Entry**: `run.py` → `app/__init__.py:create_app()` (app factory)
2. **Blueprints**: auth, courses, assignments, submissions, telemetry_api
3. **Database**: SQLite via SQLAlchemy, created on first run
4. **Course Loading**: On startup, `app/models/seed.py` calls `app/parsers/loader.py` which parses plain-text files from `assessments/courses/*/`

### Key Directories

- `app/routes/` - Flask blueprints (auth, courses, assignments, submissions, telemetry_api)
- `app/models/` - SQLAlchemy models (User, Course, Enrollment, Assignment, Question, Submission, Answer, DiscussionPost)
- `app/parsers/` - Parse plain-text assessment files into database records
- `app/telemetry/` - Request middleware and storage for JSONL logs
- `assessments/courses/` - Plain-text course and assignment definitions
- `data/` - Runtime data (lms.db, telemetry.jsonl, behavioral_telemetry.jsonl)

### Telemetry System

Two telemetry streams for AI detection research:

1. **Request telemetry** (`app/telemetry/middleware.py`): Logs all HTTP requests to `data/telemetry.jsonl`
2. **Behavioral telemetry** (`app/static/js/telemetry.js`): Client-side events (clicks, scroll, question timing) posted to `/api/telemetry/events` and stored in `data/behavioral_telemetry.jsonl`

### Data Model Relationships

- User → Enrollments → Courses
- Course → Assignments → Questions (for quizzes)
- User + Assignment → Submission → Answers (one submission per user per assignment)
- Assignment → DiscussionPosts (threaded via parent_id)

### Assessment File Format

Files in `assessments/courses/<COURSE>/` use headers (TITLE, TYPE, POINTS, etc.) followed by `---` separator and content. See existing files for examples of quiz, essay, and discussion formats.
