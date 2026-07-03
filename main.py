# CV parsing endpoint - accepts raw CV text and job role, returns structured JSON

from pydantic import BaseModel , Field

class CVUploadRequest(BaseModel):
    cv_text: str = Field(min_length=20)
    job_role: str = Field(min_length=2)


import os
import json
from fastapi import FastAPI , Header, HTTPException , Depends
from dotenv import load_dotenv
from fastapi import Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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

    return {"message": "HR interview system - Version A"}


@app.post("/parse-cv")
@limiter.limit("5/minute")
def parse_cv(request: Request, payload: CVUploadRequest, auth: None = Depends(verify_api_key)):
    logger.info(f"CV parse requested for role: {payload.job_role}")
    result = fake_claude_call(payload.cv_text)
    result["job_role_applied_for"] = payload.job_role
    return result

@app.get("/health")
def health_check():
    return {"status": "ok"}