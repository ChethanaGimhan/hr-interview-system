// One interview question with its rubric. Used both on the page that just
// generated a questionnaire and on the page that loads a saved one.

const CATEGORY_STYLES = {
  verification: "bg-blue-100 text-blue-800",
  technical: "bg-purple-100 text-purple-800",
  gap: "bg-amber-100 text-amber-800",
  behavioral: "bg-green-100 text-green-800",
};

export default function QuestionCard({ question, number }) {
  const badge = CATEGORY_STYLES[question.category] || "bg-slate-100 text-slate-700";

  return (
    <li className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <h3 className="font-medium leading-relaxed">
          {number}. {question.question_text}
        </h3>
        <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${badge}`}>
          {question.category}
        </span>
      </div>

      <p className="mt-3 text-sm text-slate-600">
        <span className="font-medium text-slate-700">Why ask this: </span>
        {question.reason}
      </p>

      <div className="mt-4 grid gap-5 sm:grid-cols-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-green-700">
            A strong answer covers
          </p>
          <ul className="mt-2 space-y-1.5 text-sm text-slate-700">
            {question.rubric.strong_answer_covers.map((point, index) => (
              <li key={index} className="flex gap-2">
                <span className="text-green-600">+</span>
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-red-700">
            Signs of a weak answer
          </p>
          <ul className="mt-2 space-y-1.5 text-sm text-slate-700">
            {question.rubric.weak_answer_signs.map((sign, index) => (
              <li key={index} className="flex gap-2">
                <span className="text-red-600">-</span>
                <span>{sign}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <p className="mt-4 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">
        <span className="font-medium">If they answer well, follow up with: </span>
        {question.rubric.follow_up_probe}
      </p>
    </li>
  );
}
