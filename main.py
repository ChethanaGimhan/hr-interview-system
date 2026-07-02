import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("ANTHROPIC_API_KEY")
print("Key loaded:", api_key is not None)

import json

def fake_claude_call(cv_text):
    """
    Placeholder — this is where the real Claude API call goes later.
    For now, it just returns a hardcoded example matching our schema.
    """
    return {
        "name": "Nimal Perera",
        "experience_years": 2,
        "skills": ["Python", "Docker"],
        "education": {
            "degree": "BSc Computer Science",
            "university": "University of Moratuwa"
        },
        "projects": [
            {"title": "AgriSenseNet", "description": "IoT + backend platform for farm monitoring"}
        ],
        "job_role_applied_for": "Software Engineer Intern"
    }

def main():
    cv_text = "some raw CV text would go here, extracted from a PDF"
    parsed = fake_claude_call(cv_text)
    print(json.dumps(parsed, indent=2))

if __name__ == "__main__":
    main()