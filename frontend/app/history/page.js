import Link from "next/link";

import { backendFetch } from "../lib/backend";

export const metadata = {
  title: "History | HR Interview System",
};

function formatDate(value) {
  return new Date(value).toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// No "use client" here on purpose. This page runs on the server, so it can call
// the backend itself and send the finished HTML to the browser. There is
// nothing to click, so there is no reason to ship it any JavaScript.
export default async function History() {
  let interviews = null;

  try {
    const response = await backendFetch("/interviews");
    if (response.ok) {
      interviews = await response.json();
    }
  } catch {
    // Leave interviews as null and show the message below.
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">History</h1>
        <p className="mt-2 text-slate-600">
          Questionnaires that have already been generated. Opening one costs
          nothing, because the questions are read from the database rather than
          written again.
        </p>
      </div>

      {interviews === null && (
        <p className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          Could not load the saved questionnaires. Is the backend running?
        </p>
      )}

      {interviews && interviews.length === 0 && (
        <p className="rounded-lg border border-slate-200 bg-white px-4 py-6 text-center text-sm text-slate-600">
          Nothing saved yet.{" "}
          <Link href="/" className="font-medium underline">
            Generate the first one
          </Link>
          .
        </p>
      )}

      {interviews && interviews.length > 0 && (
        <ul className="divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
          {interviews.map((interview) => (
            <li key={interview.id}>
              <Link
                href={`/interviews/${interview.id}`}
                className="flex flex-wrap items-center justify-between gap-2 px-5 py-4 hover:bg-slate-50"
              >
                <div>
                  <p className="font-medium">{interview.candidate_name}</p>
                  <p className="text-sm text-slate-600">{interview.job_role}</p>
                </div>
                <div className="text-right text-sm text-slate-500">
                  <p>{interview.question_count} questions</p>
                  <p>{formatDate(interview.created_at)}</p>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
