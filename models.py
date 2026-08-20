# Pydantic models: the request bodies we accept, and the JSON shapes the LLM
# has to return.
#
# The output models below are converted into a JSON Schema and sent to the LLM,
# and that conversion only supports plain types, enums and nesting. Constraints
# like min_length are dropped silently during the conversion - no error - so
# putting one on an output model gives you validation you do not actually have.
# Only the request models carry constraints, because FastAPI really does check
# those.

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# --- requests ---

class CVUploadRequest(BaseModel):
    cv_text: str = Field(min_length=20, max_length=50000)
    job_role: str = Field(min_length=2, max_length=200)


class GenerateQuestionsRequest(BaseModel):
    cv_text: str = Field(min_length=20, max_length=50000)
    job_role: str = Field(min_length=2, max_length=200)
    # Optional, but without it we can only ask "tell me about project X"
    # questions - gap questions need to know what the job actually requires.
    job_description: Optional[str] = Field(default=None, max_length=20000)
    question_count: int = Field(default=8, ge=4, le=15)


# --- what the CV parser returns ---

class Education(BaseModel):
    degree: str
    university: str


class Project(BaseModel):
    title: str
    description: str


class ParsedCV(BaseModel):
    name: str
    experience_years: int
    skills: List[str]
    education: Education
    projects: List[Project]
    job_role_applied_for: str


# --- what the question generator returns ---

class Rubric(BaseModel):
    # A rubric instead of one "correct answer", so the model can't invent a
    # fake ground truth for an open-ended question.
    strong_answer_covers: List[str]
    weak_answer_signs: List[str]
    follow_up_probe: str


class InterviewQuestion(BaseModel):
    question_text: str
    category: Literal["verification", "technical", "gap", "behavioral"]
    reason: str
    rubric: Rubric


class QuestionSet(BaseModel):
    questions: List[InterviewQuestion]


# --- what /generate-questions sends back ---

class InterviewPackage(BaseModel):
    # Filled in once the questionnaire is saved, so the caller can come back to
    # it later instead of paying for the two LLM calls again.
    interview_id: Optional[int] = None
    candidate: ParsedCV
    questions: List[InterviewQuestion]


# --- what the saved questionnaires look like coming back out ---

class InterviewSummary(BaseModel):
    id: int
    candidate_name: str
    job_role: str
    created_at: datetime
    question_count: int


class InterviewDetail(BaseModel):
    # Only the parts of the candidate that are worth keeping next to the
    # questions. Education and projects are used to write the questions and
    # then not needed again, so they are not stored.
    id: int
    candidate_name: str
    job_role: str
    experience_years: int
    skills: List[str]
    created_at: datetime
    questions: List[InterviewQuestion]
