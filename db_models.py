# The database tables. Separate from models.py, which holds the Pydantic shapes
# used for requests and for the LLM output - those two jobs look similar but
# they are not the same thing.

from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True)
    candidate_name = Column(String(200), nullable=False)
    job_role = Column(String(200), nullable=False, index=True)
    experience_years = Column(Integer, nullable=False)
    # Skills are only ever read as a whole list next to the candidate, never
    # searched on their own, so one JSON column beats a second table here.
    skills = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    questions = relationship(
        "Question", back_populates="interview", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    category = Column(String(20), nullable=False)
    reason = Column(Text, nullable=False)
    # The rubric is three lists that are always shown together with the
    # question, so it goes in one JSON column rather than three more tables.
    rubric = Column(JSON, nullable=False)

    interview = relationship("Interview", back_populates="questions")
