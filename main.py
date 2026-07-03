from pydantic import BaseModel , Field

class CVUploadRequest(BaseModel):
    cv_text: str = Field(min_length=20)
    job_role: str = Field(min_length=2)


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
def parse_cv(request: CVUploadRequest):
    result = fake_claude_call(request.cv_text)
    result["job_role_applied_for"] = request.job_role
    return result