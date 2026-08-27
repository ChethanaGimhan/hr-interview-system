"use client";

import Link from "next/link";
import { useState } from "react";

import CandidateCard from "./components/CandidateCard";
import QuestionCard from "./components/QuestionCard";

// FastAPI sends a string in detail for the errors we raise ourselves, and a
// list of problems when Pydantic rejects the request, so both shapes turn up.
function errorMessage(body) {
  if (typeof body.detail === "string") {
    return body.detail;
  }
  if (Array.isArray(body.detail) && body.detail.length > 0) {
    return body.detail[0].msg;
  }
  return "Something went wrong";
}

export default function Home() {
  const [cvText, setCvText] = useState("");
  const [jobRole, setJobRole] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [questionCount, setQuestionCount] = useState(8);

  const [reading, setReading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  async function handleFileChange(event) {
    const file = event.target.files[0];
    if (!file) {
      return;
    }

    setError("");
    setResult(null);
    setReading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("/api/upload", { method: "POST", body: formData });
      const body = await response.json();

      if (response.ok) {
        setCvText(body.cv_text);
      } else {
        setCvText("");
        setError(errorMessage(body));
      }
    } catch {
      setError("Could not reach the server");
    } finally {
      setReading(false);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setResult(null);
    setGenerating(true);

    try {
      const response = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cv_text: cvText,
          job_role: jobRole,
          job_description: jobDescription || null,
          question_count: Number(questionCount),
        }),
      });
      const body = await response.json();

      if (response.ok) {
        setResult(body);
      } else {
        setError(errorMessage(body));
      }
    } catch {
      setError("Could not reach the server");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">New questionnaire</h1>
        <p className="mt-2 text-slate-600">
          Upload a candidate CV and describe the role. You get back a profile of
          the candidate and a set of interview questions, each one with a rubric
          instead of a single correct answer.
        </p>
      </div>

      {error && (
        <p className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      )}

      <form
        onSubmit={handleSubmit}
        className="space-y-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
      >
        <div>
          <label htmlFor="cv" className="block text-sm font-medium">
            Candidate CV
          </label>
          <input
            id="cv"
            name="cv"
            type="file"
            accept="application/pdf"
            onChange={handleFileChange}
            className="mt-2 block w-full cursor-pointer rounded-md border border-slate-300 p-2 text-sm file:mr-4 file:rounded file:border-0 file:bg-slate-100 file:px-3 file:py-1.5 file:text-slate-700 hover:file:bg-slate-200"
          />
          <p className="mt-1 text-xs text-slate-500">
            PDF only, up to 5 MB. A scanned CV will not work, because there is no
            text in it to read.
          </p>
        </div>

        {reading && <p className="text-sm text-slate-600">Reading the CV...</p>}

        {cvText && (
          <div>
            <label htmlFor="cvText" className="block text-sm font-medium">
              Text we read from the CV
            </label>
            {/* Editable, because pulling text out of a PDF is not perfect and
                it is easier to fix a line here than to fix the PDF. */}
            <textarea
              id="cvText"
              rows={8}
              value={cvText}
              onChange={(event) => setCvText(event.target.value)}
              className="mt-2 block w-full rounded-md border border-slate-300 px-3 py-2 font-mono text-xs focus:border-slate-500 focus:outline-none"
            />
            <p className="mt-1 text-xs text-slate-500">
              {cvText.length} characters. Fix anything the reader got wrong
              before generating.
            </p>
          </div>
        )}

        <div>
          <label htmlFor="jobRole" className="block text-sm font-medium">
            Job role
          </label>
          <input
            id="jobRole"
            name="jobRole"
            type="text"
            required
            value={jobRole}
            onChange={(event) => setJobRole(event.target.value)}
            placeholder="Backend Engineer Intern"
            className="mt-2 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
          />
        </div>

        <div>
          <label htmlFor="jobDescription" className="block text-sm font-medium">
            Job description
          </label>
          <textarea
            id="jobDescription"
            name="jobDescription"
            rows={5}
            value={jobDescription}
            onChange={(event) => setJobDescription(event.target.value)}
            placeholder="What the role actually needs. Without this the questions can only be about what is already on the CV."
            className="mt-2 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
          />
        </div>

        <div>
          <label htmlFor="questionCount" className="block text-sm font-medium">
            Number of questions
          </label>
          <input
            id="questionCount"
            name="questionCount"
            type="number"
            min={4}
            max={15}
            value={questionCount}
            onChange={(event) => setQuestionCount(event.target.value)}
            className="mt-2 block w-24 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
          />
        </div>

        <button
          type="submit"
          disabled={!cvText || reading || generating}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {generating ? "Generating..." : "Generate questions"}
        </button>

        {generating && (
          <p className="text-sm text-slate-600">
            This takes about 45 seconds. The CV is read into a profile first, and
            then the questions are written from that profile.
          </p>
        )}
      </form>

      {result && (
        <div className="space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold">
                {result.questions.length} questions to ask
              </h2>
              <Link
                href={`/interviews/${result.interview_id}`}
                className="text-sm text-slate-500 underline"
              >
                Saved as questionnaire #{result.interview_id}
              </Link>
            </div>
            <a
              href={`/api/interviews/${result.interview_id}/pdf`}
              className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium hover:bg-slate-50"
            >
              Download as PDF
            </a>
          </div>

          <CandidateCard candidate={result.candidate} />

          <ol className="space-y-4">
            {result.questions.map((question, index) => (
              <QuestionCard key={index} question={question} number={index + 1} />
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
