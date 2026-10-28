import json
import os
import sys
import time
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from playwright.sync_api import sync_playwright

class JobEvaluation(BaseModel):
    target_track: str = Field(description="Target role category, e.g., 'IT Support / Systems' or 'Cloud / DevOps'")
    fit_score: int = Field(description="Match score 0-100 based strictly on candidate profile overlap")
    matching_skills: list[str] = Field(description="Skills that directly match the job requirements")
    missing_skills: list[str] = Field(description="Skills required by the job but missing from candidate profile")
    drafted_pitch: str = Field(description="2-3 sentence tailored pitch answering why you are a good fit using real project metrics")

def load_profile():
    with open("profile.json", "r") as f:
        return json.load(f)

def evaluate_job(profile, job_text):
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    prompt = f"""
Compare this Candidate Profile against the Target Job Description.
Never fabricate skills or metrics not listed in the profile.

Profile:
{json.dumps(profile, indent=2)}

Job Description:
{job_text}
"""
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=JobEvaluation,
        ),
    )
    return json.loads(response.text)

def apply_to_job(profile, target_url, pitch):
    print(f"\n[1/4] Launching browser for: {target_url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=60)
        page = browser.new_page()
        page.goto(target_url, wait_until="domcontentloaded")

        print("[2/4] Pre-filling candidate info...")
        full_name = profile.get("name", "")
        parts = full_name.split()
        first_name = parts[0] if parts else ""
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

        field_mappings = [
            ("input[name*='first_name' i], input[id*='first_name' i], input[placeholder*='first' i]", first_name),
            ("input[name*='last_name' i], input[id*='last_name' i], input[placeholder*='last' i]", last_name),
            ("input[name*='full_name' i], input[id*='full_name' i], input[name='name' i]", full_name),
            ("input[type='email' i], input[name*='email' i], input[id*='email' i]", profile["contact"]["email"]),
            ("input[type='tel' i], input[name*='phone' i], input[id*='phone' i]", profile["contact"]["phone"]),
            ("input[name*='linkedin' i], input[id*='linkedin' i]", profile["contact"]["linkedin"]),
            ("input[name*='github' i], input[id*='github' i]", profile["contact"]["github"]),
        ]

        for selector, value in field_mappings:
            try:
                locator = page.locator(selector)
                if locator.count() > 0:
                    locator.first.fill(value)
            except Exception:
                pass

        if pitch:
            try:
                pitch_box = page.locator("textarea[name*='cover' i], textarea[name*='comments' i], textarea[id*='additional' i], textarea[name*='summary' i], textarea")
                if pitch_box.count() > 0:
                    pitch_box.first.fill(pitch)
            except Exception:
                pass

        print("[3/4] Checking for resume attachment field...")
        resume_path = os.path.abspath("resume.pdf")
        if os.path.exists(resume_path):
            try:
                file_input = page.locator("input[type='file']")
                if file_input.count() > 0:
                    file_input.first.set_input_files(resume_path)
                    print("📎 Attached resume.pdf successfully.")
            except Exception as e:
                print(f"File upload note: {e}")
        else:
            print("Note: Place 'resume.pdf' in the project directory to auto-attach resumes.")

        print("\n" + "="*50)
        print("✋ [4/4] HUMAN-IN-THE-LOOP APPROVAL GATE")
        print("Review the filled data and adjust any custom questions.")
        print("="*50)

        choice = input("\nReady to submit this application? (y/n): ").strip().lower()

        if choice == "y":
            print("\nSubmitting application...")
            submit_btn = page.locator("button[type='submit'], input[type='submit'], button:has-text('Submit'), button:has-text('Apply')")
            if submit_btn.count() > 0:
                submit_btn.first.click()
                time.sleep(3)
                page.screenshot(path="submission_confirmation.png")
                print("✅ Submitted! Screenshot saved as 'submission_confirmation.png'.")
            else:
                print("⚠️ Submit button not detected automatically. Please click it manually in the browser.")
                input("Press Enter when you have manually submitted...")
        else:
            print("❌ Submission cancelled. No data submitted.")

        browser.close()

if __name__ == "__main__":
    profile = load_profile()

    print("--- Job Copilot AI Engine ---")
    user_url = input("Enter job application URL (or press Enter to test standard form): ").strip()
    if not user_url:
        user_url = "https://httpbin.org/forms/post"

    job_description_input = input("\nPaste key job requirements/text (or press Enter for sample cloud role): ").strip()
    if not job_description_input:
        job_description_input = """
        Junior Systems & Cloud Administrator:
        Looking for candidates with hands-on Linux experience, basic AWS (EC2/VPC), 
        and familiarity with Terraform or automation scripting. Good customer troubleshooting skills.
        """

    print("\nAnalyzing job description with Gemini...")
    eval_result = evaluate_job(profile, job_description_input)

    print("\n" + "="*45)
    print(f"TRACK IDENTIFIED: {eval_result['target_track']}")
    print(f"FIT SCORE:        {eval_result['fit_score']}/100")
    print(f"MATCHING SKILLS:  {', '.join(eval_result['matching_skills'])}")
    print(f"DRAFTED PITCH:\n{eval_result['drafted_pitch']}")
    print("="*45)

    apply_to_job(profile, user_url, eval_result['drafted_pitch'])
