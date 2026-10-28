import json
import time
from playwright.sync_api import sync_playwright

with open("profile.json", "r") as f:
    profile = json.load(f)

def run_application(job_url, custom_pitch=""):
    print(f"\n[1/3] Launching browser for: {job_url}")
    
    with sync_playwright() as p:
        # headless=False lets you see the browser open live
        browser = p.chromium.launch(headless=False, slow_mo=50)
        page = browser.new_page()
        page.goto(job_url, wait_until="networkidle")

        print("[2/3] Pre-filling candidate info...")

        # Split name for ATS forms that require separate First/Last
        full_name = profile.get("name", "")
        parts = full_name.split()
        first_name = parts[0] if parts else ""
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

        # Field definitions covering common ATS platforms (Lever, Greenhouse, Ashby, Workable)
        field_mappings = [
            ("input[name*='first_name' i], input[id*='first_name' i]", first_name),
            ("input[name*='last_name' i], input[id*='last_name' i]", last_name),
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

        # Fill cover letter / custom pitch if a suitable text box exists
        if custom_pitch:
            try:
                pitch_box = page.locator("textarea[name*='cover' i], textarea[name*='comments' i], textarea[id*='additional' i], textarea[name*='summary' i]")
                if pitch_box.count() > 0:
                    pitch_box.first.fill(custom_pitch)
            except Exception:
                pass

        print("\n" + "="*50)
        print("✋ [3/3] HUMAN-IN-THE-LOOP APPROVAL GATE")
        print("The browser is active on your screen.")
        print("Review the filled data and adjust any custom questions.")
        print("="*50)

        choice = input("\nReady to submit this application? (y/n): ").strip().lower()

        if choice == "y":
            print("\nSubmitting application...")
            submit_btn = page.locator("button[type='submit'], input[type='submit'], button:has-text('Submit Application'), button:has-text('Apply')")
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
    # Test launch on a standard form structure
    test_pitch = "I bring hands-on experience in AWS cloud infrastructure, Linux systems administration, and Terraform automation."
    test_url = "https://boards.greenhouse.io/embed/job_app?for=canonical&token=4042841002"
    run_application(test_url, custom_pitch=test_pitch)
