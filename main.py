# HR Interview System - takes a CV and a job role, returns a structured
# candidate profile and a tailored interview questionnaire with rubrics.

import logging
import os
import secrets

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

import llm_service
from models import CVUploadRequest, GenerateQuestionsRequest, InterviewPackage, ParsedCV

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="HR Interview System")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def verify_api_key(x_api_key: str = Header(...)):
    expected_key = os.environ.get("INTERNAL_API_KEY")
    if not expected_key:
        raise HTTPException(status_code=503, detail="Server API key is not configured")
    # compare_digest instead of != so a wrong key always takes the same time to
    # reject. A plain != returns early and leaks how many characters matched.
    if not secrets.compare_digest(x_api_key, expected_key):
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/")
def read_root():
    return {"message": "HR interview system - Version A"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/parse-cv", response_model=ParsedCV)
@limiter.limit("5/minute")
def parse_cv(request: Request, payload: CVUploadRequest, auth: None = Depends(verify_api_key)):
    logger.info(f"CV parse requested for role: {payload.job_role}")
    candidate = llm_service.parse_cv(payload.cv_text, payload.job_role)
    # Our own validated input wins over whatever the model echoed back.
    candidate.job_role_applied_for = payload.job_role
    return candidate


@app.post("/generate-questions", response_model=InterviewPackage)
@limiter.limit("3/minute")
def generate_questions(
    request: Request,
    payload: GenerateQuestionsRequest,
    auth: None = Depends(verify_api_key),
):
    # Two LLM calls: parse the CV into a profile, then write questions from
    # that profile. Tighter rate limit than /parse-cv because it costs double.
    logger.info(f"Questionnaire requested for role: {payload.job_role}")

    candidate = llm_service.parse_cv(payload.cv_text, payload.job_role)
    candidate.job_role_applied_for = payload.job_role

    question_set = llm_service.generate_questions(
        candidate, payload.job_role, payload.job_description, payload.question_count
    )
    return InterviewPackage(candidate=candidate, questions=question_set.questions)
