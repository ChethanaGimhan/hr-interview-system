# HR Interview System

![CI](https://github.com/ChethanaGimhan/hr-interview-system/actions/workflows/ci.yml/badge.svg)

Turns a candidate's CV and a job description into interview questions.

## What it does

HR teams prepare interview questions for every applicant by hand. This does it
automatically. You upload the CV as a PDF and describe the role. You get back a
profile of the candidate and a set of questions to ask. The questions can be
downloaded as a PDF to take into the interview.

```
CV.pdf + job role + job description
              |
        [ pypdf ]       ->  text pulled out of the PDF
              |
       [ LLM call 1 ]   ->  candidate profile
              |
       [ LLM call 2 ]   ->  questions + rubrics
              |
       [ PostgreSQL ]   ->  saved, so opening it again is free
              |
       [ fpdf2 ]        ->  downloadable questionnaire
```

There are two LLM calls instead of one. The second call gets a clean profile to
work from, and the questions come out better that way.

Each question has a category and a rubric. The rubric lists what a strong answer
covers and what a weak answer looks like. There is no "correct answer" field,
because for an open question the model would just invent one.

| Category | Purpose |
|---|---|
| `verification` | Check a claim made on the CV |
| `technical` | Test depth in a skill the role needs |
| `gap` | Something the role needs that the CV does not show |
| `behavioral` | Teamwork, conflict, ownership |

Gap questions only work if you send the job description.

## How it is put together

```
              browser
                 |
            [ Ingress ]                only way in
                 |
        [ Next.js frontend ]           adds the API key
                 |
        [ FastAPI backend ]            LLM calls, PDF handling, rate limits
                 |
        [ PostgreSQL + PVC ]           survives the pod being deleted
```

The browser never calls the backend. It calls the frontend's own server, and
that server adds the `x-api-key` header before passing the request on. The
browser can read anything that gets sent to it, so the key is never sent there.

## Tech stack

| Part | Used for |
|---|---|
| FastAPI, Pydantic | API and request validation |
| Gemini or Claude | CV parsing and question writing |
| SQLAlchemy, PostgreSQL | Storing questionnaires |
| pypdf, fpdf2 | Reading CVs in, writing questionnaires out |
| Next.js, React, Tailwind | The web app |
| Docker, Docker Compose | Running it |
| GitHub Actions, Trivy, GHCR | Build, scan, publish |
| Kubernetes, ingress-nginx | Deployment |

The LLM provider is set with the `LLM_PROVIDER` environment variable, so it can
be switched without changing code.

## API

All endpoints except `/` and `/health` need an `x-api-key` header.

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check, used by the Kubernetes probes |
| `POST` | `/upload-cv` | PDF upload, returns the text found in it |
| `POST` | `/parse-cv` | CV text to structured profile |
| `POST` | `/generate-questions` | CV and job description to questions, saved |
| `GET` | `/interviews` | The saved questionnaires, newest first |
| `GET` | `/interviews/{id}` | One saved questionnaire |
| `GET` | `/interviews/{id}/pdf` | The same questionnaire as a PDF |

Interactive docs are at `/docs` when it is running.

## Running it locally

```bash
git clone https://github.com/ChethanaGimhan/hr-interview-system.git
cd hr-interview-system
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill it in. A Gemini key is free and does not
need a card: https://aistudio.google.com/apikey

Backend, in one terminal:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000
```

Frontend, in another one. Copy `frontend/.env.example` to
`frontend/.env.local` first. Use the same `INTERNAL_API_KEY` on both sides or
every request will come back 401.

```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:3000. If you only want the API, it is at
http://127.0.0.1:8000/docs.

## Running with Docker Compose

This starts Postgres, the backend and the frontend together. The backend waits
until Postgres can actually accept a connection before it starts.

```bash
docker compose up --build
```

Open http://localhost:3000. `docker compose down` stops everything and keeps
the data. Add `-v` to delete the data as well.

## Running on Kubernetes

Create the config and credentials first:

```bash
kubectl create secret generic postgres-secret --from-literal=POSTGRES_PASSWORD=<password>
kubectl create secret generic app-secrets --from-literal=INTERNAL_API_KEY=<key> --from-literal=GEMINI_API_KEY=<key> --from-literal=DATABASE_URL=postgresql://postgres:<password>@postgres-service:5432/hr_interview
kubectl create configmap app-config --from-literal=LLM_PROVIDER=gemini --from-literal=GEMINI_MODEL=gemini-3.5-flash
kubectl create secret docker-registry ghcr-secret --docker-server=ghcr.io --docker-username=<username> --docker-password=<token with read:packages>
```

The last one is needed because the images are in private GHCR packages.

An ingress controller has to be installed too. `ingress.yaml` on its own does
nothing. It is only a description, and the controller is the program that reads
it and acts on it.

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.15.1/deploy/static/provider/cloud/deploy.yaml
kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=120s
```

Then:

```bash
kubectl apply -f postgres-deployment.yaml
kubectl apply -f app-deployment.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f ingress.yaml
```

Open http://localhost. Only the frontend can be reached from outside. The
backend and the database are ClusterIP services, so they are only reachable
from inside the cluster. To call the API directly:

```bash
kubectl port-forward service/hr-app-service 8080:8080
```

## Tests

```bash
pytest
```

The LLM calls are mocked. The tests do not need an API key and they give the
same result every time. They cover validation, authentication, the response
shape, the upload limits, saving and reading back, and the PDF download.

## Security

- Every endpoint needs an API key in the `x-api-key` header
- Pydantic checks every request body and sends back a 422 if a field is missing
  or the wrong type
- Rate limits: 10/min on `/upload-cv`, 5/min on `/parse-cv`, 3/min on
  `/generate-questions`. `/generate-questions` is the tightest because it makes
  two LLM calls
- Uploads stop at 5 MB. The file is read 64 KB at a time and thrown away as soon
  as it goes over, instead of loading all of it into memory first. A 200 MB test
  upload took the process from 80 MB to 470 MB before this was fixed, and the
  pod only gets 512Mi
- A file is only treated as a PDF if it starts with `%PDF-`. Anyone can rename a
  file to `cv.pdf`, so the name is not proof of anything
- Both containers run as a non-root user, and npm is removed from the frontend
  image because it is only needed to build, not to run
- Trivy scans both images in CI and fails the build if it finds a CRITICAL or
  HIGH problem that has a fix available
- Errors from the LLM provider are logged in full but returned as a generic
  message

## Known limitations

- The free Gemini tier may use submitted data for training. A CV is personal
  data, so this is only used with made-up candidates. Real use would need a paid
  tier or a self-hosted model.
- Generating takes about 45 seconds because of the two LLM calls. The page shows
  progress while it waits, but this should really be a background job.
- The schema makes the model fill in the right fields. It does not make the
  values right. While testing it read "2 years part time" as 0 years of
  experience. This is why every question comes with a rubric and no correct
  answer.
- Scanned CVs do not work. There is no text in them to pull out, and OCR is out
  of scope.
- One shared API key. There are no user accounts.
- Tables are created with `create_all` when the app starts. That can add a new
  table but it cannot change one that already exists, so a real deployment would
  need migrations.
- The tests run on SQLite while the cluster runs Postgres. It is fast, but a
  difference between the two databases would not be caught.

## Background

This started as a group project with three Data Science students. They were
going to do the CV parsing and the question generation prompts, and I was doing
the architecture, backend, DevOps and security. They stopped contributing
partway through, so I finished the rest myself.
