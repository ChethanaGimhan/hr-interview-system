// The short profile of the candidate that sits above the questions, so the
// interviewer has the basics in front of them without opening the CV again.

export default function CandidateCard({ candidate }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-xl font-semibold">{candidate.name}</h2>
        <p className="text-sm text-slate-600">
          {candidate.job_role_applied_for}
        </p>
      </div>

      <p className="mt-1 text-sm text-slate-600">
        {candidate.experience_years} years of experience
      </p>

      <div className="mt-4 flex flex-wrap gap-2">
        {candidate.skills.map((skill) => (
          <span
            key={skill}
            className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700"
          >
            {skill}
          </span>
        ))}
      </div>

      {candidate.education && (
        <p className="mt-4 text-sm text-slate-700">
          {candidate.education.degree}, {candidate.education.university}
        </p>
      )}

      {candidate.projects && candidate.projects.length > 0 && (
        <ul className="mt-3 space-y-1 text-sm text-slate-700">
          {candidate.projects.map((project) => (
            <li key={project.title}>
              <span className="font-medium">{project.title}</span> -{" "}
              {project.description}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
