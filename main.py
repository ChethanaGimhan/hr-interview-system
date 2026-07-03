import os
import json
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

def fake_claude_call(cv_text):
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

@app.get("/")
def read_root():
    return {"message": "HR interview system is running"}

@app.post("/parse-cv")
def parse_cv():
    cv_text = "some raw CV text would go here"
    result = fake_claude_call(cv_text)
    return result