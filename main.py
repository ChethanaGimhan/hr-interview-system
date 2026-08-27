# HR Interview System - takes a CV and a job role, returns a structured
# candidate profile and a tailored interview questionnaire with rubrics.

import logging
import os
import secrets
from typing import List

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response, UploadFile
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

import database
import db_models
import llm_service
import pdf_export
import pdf_service
from models import (
    CVUploadRequest,
    GenerateQuestionsRequest,
    InterviewDetail,
    InterviewPackage,
    InterviewSummary,
    ParsedCV,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="HR Interview System")

# Create the tables on startup if they are not there already. That is enough
# for a project this size, but it can only add tables, never change one that
# already exists. A real deployment would use a migration tool for that.
db_models.Base.metadata.create_all(bind=database.engine)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 5 MB is far more than any real CV needs, and small enough that even a burst
# of uploads cannot fill the 512Mi this pod gets in Kubernetes.
MAX_CV_BYTES = 5 * 1024 * 1024
CHUNK_SIZE = 64 * 1024


async def read_upload(file: UploadFile) -> bytes:
    # Read a piece at a time and give up as soon as the total goes over the
    # limit. file.read() with no argument pulls the whole upload into memory
    # first, and a 200MB test file took this process from 80MB to 470MB.
    chunks = []
    total = 0
    while True:
        chunk = await file.read(CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_CV_BYTES:
            raise HTTPException(status_code=413, detail="CV file is too large, the limit is 5 MB")
        chunks.append(chunk)
    return b"".join(chunks)


def save_interview(db: Session, package: InterviewPackage) -> db_models.Interview:
    interview = db_models.Interview(
        candidate_name=package.candidate.name,
        job_role=package.candidate.job_role_applied_for,
        experience_years=package.candidate.experience_years,
        skills=package.candidate.skills,
        questions=[
            db_models.Question(
                question_text=question.question_text,
                category=question.category,
                reason=question.reason,
                rubric=question.rubric.model_dump(),
            )
            for question in package.questions
        ],
    )
    db.add(interview)
    # One commit for the interview and all of its questions together, so a
    # crash halfway through cannot leave a questionnaire with no questions.
    db.commit()
    db.refresh(interview)
    return interview


def find_interview(db: Session, interview_id: int) -> db_models.Interview:
    interview = db.get(db_models.Interview, interview_id)
    if interview is None:
        raise HTTPException(status_code=404, detail="No questionnaire with that id")
    return interview


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


@app.post("/upload-cv")
@limiter.limit("10/minute")
async def upload_cv(request: Request, file: UploadFile, auth: None = Depends(verify_api_key)):
    # Reading the PDF is fast and free, so it gets its own endpoint. The slow,
    # paid LLM call stays in /generate-questions, which means a failure there
    # does not cost the user another upload.
    contents = await read_upload(file)
    cv_text = pdf_service.extract_text(contents)
    logger.info(f"Read {len(cv_text)} characters out of the uploaded CV")
    return {"cv_text": cv_text}


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
    db: Session = Depends(database.get_db),
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
    package = InterviewPackage(candidate=candidate, questions=question_set.questions)

    # Saved so the same questionnaire can be opened again later without paying
    # for another 45 seconds of LLM calls.
    saved = save_interview(db, package)
    package.interview_id = saved.id
    return package


@app.get("/interviews", response_model=List[InterviewSummary])
def list_interviews(
    db: Session = Depends(database.get_db),
    auth: None = Depends(verify_api_key),
):
    # Newest first, and capped, because nobody scrolls past the last 50 and an
    # uncapped list gets slower every time the app is used.
    rows = (
        db.query(db_models.Interview)
        .order_by(db_models.Interview.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        InterviewSummary(
            id=row.id,
            candidate_name=row.candidate_name,
            job_role=row.job_role,
            created_at=row.created_at,
            question_count=len(row.questions),
        )
        for row in rows
    ]


@app.get("/interviews/{interview_id}", response_model=InterviewDetail)
def get_interview(
    interview_id: int,
    db: Session = Depends(database.get_db),
    auth: None = Depends(verify_api_key),
):
    interview = find_interview(db, interview_id)

    return InterviewDetail(
        id=interview.id,
        candidate_name=interview.candidate_name,
        job_role=interview.job_role,
        experience_years=interview.experience_years,
        skills=interview.skills,
        created_at=interview.created_at,
        questions=[
            {
                "question_text": question.question_text,
                "category": question.category,
                "reason": question.reason,
                "rubric": question.rubric,
            }
            for question in interview.questions
        ],
    )


@app.get("/interviews/{interview_id}/pdf")
def download_interview_pdf(
    interview_id: int,
    db: Session = Depends(database.get_db),
    auth: None = Depends(verify_api_key),
):
    interview = find_interview(db, interview_id)
    document = pdf_export.build_questionnaire_pdf(interview)

    filename = f"{pdf_export.safe_filename(interview.candidate_name)}_questions.pdf"
    return Response(
        content=document,
        media_type="application/pdf",
        # attachment makes the browser save the file instead of showing it, and
        # filename is the name it saves it under.
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
