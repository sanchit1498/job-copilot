import json
import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

class JobEvaluation(BaseModel):
    target_track: str = Field(description="Target role category, e.g., 'IT Support / Systems' or 'Cloud / DevOps'")
    fit_score: int = Field(description="Match score 0-100 based strictly on candidate profile overlap")
    matching_skills: list[str] = Field(description="Skills that directly match the job requirements")
    missing_skills: list[str] = Field(description="Skills required by the job but missing from candidate profile")
    drafted_pitch: str = Field(description="2-3 sentence tailored pitch answering why you are a good fit using real project metrics")

with open("profile.json", "r") as f:
    my_profile = json.load(f)

sample_job_desc = """
Junior Systems & Cloud Administrator:
We are seeking a junior technologist to support our Linux/AWS infrastructure and office systems.
Requirements:
- Hands-on experience with Linux (Ubuntu) and AWS core services (EC2, VPC, S3).
- Basic understanding of Infrastructure as Code (Terraform) or CI/CD pipelines.
- Experience troubleshooting networking (DNS, DHCP, TCP/IP) and hardware/workstations.
- Good communication skills for internal stakeholder support and runbook documentation.
"""

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

prompt = f"""
Compare this Candidate Profile against the Target Job Description.
Never fabricate skills or metrics not listed in the profile.

Profile:
{json.dumps(my_profile, indent=2)}

Job Description:
{sample_job_desc}
"""

response = client.models.generate_content(
    model="gemini-3.1-flash-lite",
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=JobEvaluation,
    ),
)

eval_data = json.loads(response.text)
print("\n" + "="*45)
print(f"TRACK IDENTIFIED: {eval_data['target_track']}")
print(f"FIT SCORE:        {eval_data['fit_score']}/100")
print(f"MATCHING SKILLS:  {', '.join(eval_data['matching_skills'])}")
print(f"MISSING SKILLS:   {', '.join(eval_data['missing_skills']) if eval_data['missing_skills'] else 'None'}")
print(f"DRAFTED PITCH:\n{eval_data['drafted_pitch']}")
print("="*45 + "\n")
