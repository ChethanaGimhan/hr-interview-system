from pydantic import BaseModel , Field

class CVUploadRequest(BaseModel):
    cv_text: str = Field(min_length=20)
    job_role: str = Field(min_length=2)


import os
import json
from fastapi import FastAPI , Header, HTTPException , Depends
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

def verify_api_key(x_api_key: str = Header(...)):
    expected_key = os.environ.get("INTERNAL_API_KEY")
    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

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
def parse_cv(request: CVUploadRequest, auth: None = Depends(verify_api_key)):
    result = fake_claude_call(request.cv_text)
    result["job_role_applied_for"] = request.job_role
    return result