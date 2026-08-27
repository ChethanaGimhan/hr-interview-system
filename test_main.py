import os
from pathlib import Path

# Point the app at a throwaway database before importing it, so running the
# tests never touches the real one. database.py reads this when it is imported,
# which happens on the "import main" line below.
os.environ["DATABASE_URL"] = "sqlite:///./test_hr_interview.db"

import pytest
from fastapi.testclient import TestClient

import database
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


@pytest.fixture(autouse=True)
def reset_rate_limits():
    # The rate limiter counts requests for the whole test run, and every test
    # comes from the same client address, so without this the later tests get
    # a 429 because of calls the earlier ones made.
    main.limiter.reset()


@pytest.fixture(autouse=True)
def empty_database():
    # Every test starts with empty tables, otherwise rows saved by one test
    # show up in the next one and the list test counts the wrong number.
    database.Base.metadata.drop_all(bind=database.engine)
    database.Base.metadata.create_all(bind=database.engine)


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


def generate_one(job_role="Backend Intern"):
    return client.post(
        "/generate-questions",
        headers={"x-api-key": API_KEY},
        json={"cv_text": CV_TEXT, "job_role": job_role, "question_count": 8},
    )


def test_generated_questionnaire_is_saved_and_can_be_read_back(fake_llm):
    interview_id = generate_one().json()["interview_id"]
    assert interview_id is not None

    response = client.get(f"/interviews/{interview_id}", headers={"x-api-key": API_KEY})
    assert response.status_code == 200
    body = response.json()
    assert body["candidate_name"] == "Nimal Perera"
    assert body["job_role"] == "Backend Intern"
    # The rubric has to survive the trip through the JSON column unchanged.
    assert body["questions"][0]["rubric"]["follow_up_probe"]


def test_listing_shows_the_saved_questionnaires_newest_first(fake_llm):
    generate_one("Backend Intern")
    generate_one("DevOps Intern")

    response = client.get("/interviews", headers={"x-api-key": API_KEY})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["question_count"] == 1


def test_questionnaire_downloads_as_a_pdf(fake_llm):
    interview_id = generate_one().json()["interview_id"]

    response = client.get(f"/interviews/{interview_id}/pdf", headers={"x-api-key": API_KEY})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    # The same check the upload endpoint does, only this time on a file we made
    # ourselves: a real PDF starts with %PDF-.
    assert response.content.startswith(b"%PDF-")
    assert "Nimal_Perera_questions.pdf" in response.headers["content-disposition"]


def test_a_name_with_quotes_in_it_cannot_break_the_download_header(fake_llm, monkeypatch):
    # A CV can say anything, and the candidate name ends up inside a response
    # header, so a quote or a newline in it must not survive that far.
    nasty = FAKE_CANDIDATE.model_copy(update={"name": 'Nimal" \nX-Injected: yes'})
    monkeypatch.setattr(llm_service, "parse_cv", lambda cv_text, job_role: nasty.model_copy())

    interview_id = generate_one().json()["interview_id"]
    response = client.get(f"/interviews/{interview_id}/pdf", headers={"x-api-key": API_KEY})

    assert response.status_code == 200
    assert "x-injected" not in response.headers
    # Every character that was not a letter or a number became an underscore,
    # so the quote, the space and the newline are all gone.
    assert (
        response.headers["content-disposition"]
        == 'attachment; filename="Nimal___X_Injected__yes_questions.pdf"'
    )


def test_asking_for_a_questionnaire_that_does_not_exist_returns_404():
    response = client.get("/interviews/9999", headers={"x-api-key": API_KEY})
    assert response.status_code == 404
