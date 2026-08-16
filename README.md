# HR Interview System

![CI](https://github.com/ChethanaGimhan/hr-interview-system/actions/workflows/ci.yml/badge.svg)

Generates interview questions from a candidate's CV and the job description.

## What it does

HR teams have to prepare interview questions for every applicant by hand. This
does it automatically. You send the CV text and the job description, and you get
back a structured profile of the candidate plus a set of questions to ask.

```
CV text + job role + job description
              |
       [ LLM call 1 ]  ->  candidate profile
              |
       [ LLM call 2 ]  ->  questions + rubrics
              |
           JSON response
```

Two calls instead of one, because the second call produces better questions from
a clean profile than from raw CV text.

Each question has a category and a rubric. The rubric says what a strong answer
covers and what a weak answer looks like, instead of giving one "correct
answer" - the model would just make one up for open questions.

| Category | Purpose |
|---|---|
| `verification` | Check a claim made on the CV |
| `technical` | Test depth in a skill the role needs |
| `gap` | Something the role needs that the CV does not show |
| `behavioral` | Teamwork, conflict, ownership |

Gap questions only work if you send the job description.

## Tech stack

FastAPI, Pydantic, Gemini (or Claude), PostgreSQL, Docker, GitHub Actions,
Trivy, GHCR, Kubernetes.

The LLM provider is set with the `LLM_PROVIDER` environment variable, so it can
be switched without changing code.

## API

All endpoints except `/` and `/health` need an `x-api-key` header.

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check, used by the Kubernetes probes |
| `POST` | `/parse-cv` | CV text to structured profile |
| `POST` | `/generate-questions` | CV and job description to questions |

Interactive docs are at `/docs` when it is running.

## Running it locally

```bash
git clone https://github.com/ChethanaGimhan/hr-interview-system.git
cd hr-interview-system
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill it in. A Gemini key is free and does not
need a card: https://aistudio.google.com/apikey

```bash
uvicorn main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs and try `/generate-questions`.

## Running with Docker Compose

Starts the app and Postgres together. The named volume keeps the database data
between restarts.

```bash
docker compose up -d
docker compose down
```

## Running on Kubernetes

Create the config and credentials first:

```bash
kubectl create secret generic postgres-secret --from-literal=POSTGRES_PASSWORD=<password>
kubectl create secret generic app-secrets --from-literal=INTERNAL_API_KEY=<key> --from-literal=GEMINI_API_KEY=<key>
kubectl create configmap app-config --from-literal=LLM_PROVIDER=gemini --from-literal=GEMINI_MODEL=gemini-3.5-flash
kubectl create secret docker-registry ghcr-secret --docker-server=ghcr.io --docker-username=<username> --docker-password=<token with read:packages>
```

The last one is needed because the image is in a private GHCR package. Then:

```bash
kubectl apply -f postgres-deployment.yaml
kubectl apply -f app-deployment.yaml
```

The service is on port 8080, not 8000, so it does not clash with uvicorn during
development.

## Tests

```bash
pytest
```

The LLM calls are mocked, so the tests do not need an API key and give the same
result every time. They cover validation, authentication and the response shape.

## Security

- Input validation with Pydantic, returns 422
- API key in the `x-api-key` header, compared with `secrets.compare_digest`
- Rate limiting: 5/min on `/parse-cv`, 3/min on `/generate-questions`
- Container runs as a non-root user
- Trivy scans the image on every push to `master`
- Secrets come from environment variables locally and Kubernetes Secrets in the
  cluster, never from the repo
- Errors from the LLM provider are logged in full but returned as a generic
  message

## Known limitations

- The free Gemini tier may use submitted data for training. A CV is personal
  data, so this is only used with made-up candidates. Real use would need a paid
  tier or a self-hosted model.
- A request takes about 45 seconds because of the two LLM calls. This should
  become a background job.
- Postgres is deployed but the app does not store anything in it yet.
- One shared API key, not user accounts.
- Trivy reports vulnerabilities but does not fail the build.
- CVs are sent as plain text, not uploaded as PDF.

## Team

Built with three Data Science and AI students. I work on the architecture,
backend, DevOps and security. They work on CV parsing and the question
generation prompts. The models in `models.py` are the agreed contract between
the two parts.
