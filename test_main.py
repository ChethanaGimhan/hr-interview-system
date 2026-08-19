from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import llm_service
import main
from models import Education, InterviewQuestion, ParsedCV, Project, QuestionSet, Rubric

client = TestClient(main.app)

API_KEY = "test-key"
CV_TEXT = "Nimal Perera. BSc Computer Science, University of Moratuwa. Python, Docker."

# A made up CV, kept next to the tests so the upload tests have a real PDF to
# send. Path is built from __file__ so pytest works from any directory.
SAMPLE_CV = Path(__file__).parent / "sample_cv.pdf"


@pytest.fixture(autouse=True)
def api_key(monkeypatch):
    monkeypatch.setenv("INTERNAL_API_KEY", API_KEY)


# Stand-ins for the LLM calls, so the tests (and CI) run without an API key
# and without spending money on every push.
FAKE_CANDIDATE = ParsedCV(
    name="Nimal Perera",
    experience_years=2,
    skills=["Python", "Docker"],
    education=Education(degree="BSc Computer Science", university="University of Moratuwa"),
    projects=[Project(title="AgriSenseNet", description="IoT platform for farm monitoring")],
    job_role_applied_for="Software Engineer Intern",
)

FAKE_QUESTIONS = QuestionSet(
    questions=[
        InterviewQuestion(
            question_text="Walk me through how you used Docker on AgriSenseNet.",
            category="technical",
            reason="Docker is listed on the CV and the role depends on it.",
            rubric=Rubric(
                strong_answer_covers=["images vs containers", "why Docker was chosen"],
                weak_answer_signs=["only repeats textbook definitions"],
                follow_up_probe="How did you keep the image size down?",
            ),
        )
    ]
)


@pytest.fixture
def fake_llm(monkeypatch):
    monkeypatch.setattr(llm_service, "parse_cv", lambda cv_text, job_role: FAKE_CANDIDATE.model_copy())
    monkeypatch.setattr(llm_service, "generate_questions", lambda *args: FAKE_QUESTIONS)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_cv_rejects_bad_api_key():
    response = client.post(
        "/upload-cv",
        headers={"x-api-key": "wrong-key"},
        files={"file": ("cv.pdf", SAMPLE_CV.read_bytes(), "application/pdf")},
    )
    assert response.status_code == 401


def test_upload_cv_returns_the_text_inside_the_pdf():
    response = client.post(
        "/upload-cv",
        headers={"x-api-key": API_KEY},
        files={"file": ("cv.pdf", SAMPLE_CV.read_bytes(), "application/pdf")},
    )
    assert response.status_code == 200
    assert "Nimal Perera" in response.json()["cv_text"]


def test_upload_cv_rejects_a_file_that_is_not_a_pdf():
    response = client.post(
        "/upload-cv",
        headers={"x-api-key": API_KEY},
        files={"file": ("cv.pdf", b"this is not a pdf at all", "application/pdf")},
    )
    assert response.status_code == 400


def test_upload_cv_rejects_an_exe_renamed_as_a_pdf():
    # A Windows .exe starts with MZ. The file name and the content type here
    # both claim it is a PDF, so the first bytes are the only thing that shows
    # what it really is.
    fake = b"MZ\x90\x00" + b"\x00" * 200
    response = client.post(
        "/upload-cv",
        headers={"x-api-key": API_KEY},
        files={"file": ("cv.pdf", fake, "application/pdf")},
    )
    assert response.status_code == 400


def test_upload_cv_rejects_a_file_over_the_size_limit():
    # Starts with %PDF- so it gets past the type check, and is bigger than the
    # 5 MB cap so the chunked read has to stop it.
    too_big = b"%PDF-1.4" + b"A" * (6 * 1024 * 1024)
    response = client.post(
        "/upload-cv",
        headers={"x-api-key": API_KEY},
        files={"file": ("cv.pdf", too_big, "application/pdf")},
    )
    assert response.status_code == 413


def test_parse_cv_rejects_bad_api_key():
    response = client.post(
        "/parse-cv",
        headers={"x-api-key": "wrong-key"},
        json={"cv_text": CV_TEXT, "job_role": "SWE"},
    )
    assert response.status_code == 401


def test_parse_cv_rejects_short_cv_text():
    response = client.post(
        "/parse-cv",
        headers={"x-api-key": API_KEY},
        json={"cv_text": "too short", "job_role": "SWE"},
    )
    assert response.status_code == 422


def test_parse_cv_returns_structured_profile(fake_llm):
    response = client.post(
        "/parse-cv",
        headers={"x-api-key": API_KEY},
        json={"cv_text": CV_TEXT, "job_role": "Backend Intern"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Nimal Perera"
    assert "Docker" in body["skills"]
    # The role we asked for, not whatever the model echoed back.
    assert body["job_role_applied_for"] == "Backend Intern"


def test_generate_questions_rejects_missing_api_key():
    response = client.post(
        "/generate-questions",
        json={"cv_text": CV_TEXT, "job_role": "SWE"},
    )
    assert response.status_code == 422  # x-api-key header is required


def test_generate_questions_returns_questions_with_rubrics(fake_llm):
    response = client.post(
        "/generate-questions",
        headers={"x-api-key": API_KEY},
        json={"cv_text": CV_TEXT, "job_role": "Backend Intern", "question_count": 8},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["candidate"]["name"] == "Nimal Perera"

    question = body["questions"][0]
    assert question["category"] in ["verification", "technical", "gap", "behavioral"]
    assert question["rubric"]["strong_answer_covers"]
    assert question["rubric"]["follow_up_probe"]
