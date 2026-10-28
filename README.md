# AI Job Application Copilot (Human-in-the-Loop)

An automated assistant that evaluates job descriptions against a candidate's profile, drafts tailored responses using Google Gemini structured outputs, and uses Playwright to pre-fill ATS application forms with a mandatory human approval gate before submission.

## Architecture
1. Ground Truth (profile.json): Structured resume and skills data.
2. AI Brain (gemini-3.1-flash-lite): Enforces structured Pydantic schemas to calculate match scores and draft tailored pitches without hallucinations.
3. Browser Automation (Playwright): Controls a local Chromium instance to pre-fill form fields.
4. Approval Gate: Execution pauses for human verification before any submission action is taken.

## Setup & Running
- Clone repository and activate venv
- Run: python3 main.py
