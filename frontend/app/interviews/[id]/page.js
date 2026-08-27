import Link from "next/link";
import { notFound } from "next/navigation";

import QuestionCard from "../../components/QuestionCard";
import { backendFetch } from "../../lib/backend";

function formatDate(value) {
  return new Date(value).toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default async function InterviewPage({ params }) {
  // params is a promise in this version of Next.js, so it has to be awaited
  // before the id can be read out of it.
  const { id } = await params;

  let response;
  try {
    response = await backendFetch(`/interviews/${encodeURIComponent(id)}`);
  } catch {
    return (
      <p className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        Could not load this questionnaire. Is the backend running?
      </p>
    );
  }

  if (response.status === 404) {
    notFound();
  }

  const interview = await response.json();

  return (
    <div className="space-y-6">
      <Link href="/history" className="text-sm text-slate-600 hover:text-slate-900">
        Back to history
      </Link>

      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h1 className="text-xl font-semibold">{interview.candidate_name}</h1>
          <p className="text-sm text-slate-600">{interview.job_role}</p>
        </div>

        <p className="mt-1 text-sm text-slate-600">
          {interview.experience_years} years of experience, saved{" "}
          {formatDate(interview.created_at)}
        </p>

        <div className="mt-4 flex flex-wrap gap-2">
          {interview.skills.map((skill) => (
            <span
              key={skill}
              className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700"
            >
              {skill}
            </span>
          ))}
        </div>
      </div>

      <h2 className="text-lg font-semibold">
        {interview.questions.length} questions to ask
      </h2>

      <ol className="space-y-4">
        {interview.questions.map((question, index) => (
          <QuestionCard key={index} question={question} number={index + 1} />
        ))}
      </ol>
    </div>
  );
}
