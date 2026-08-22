export default function Home() {
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

      <form className="space-y-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div>
          <label htmlFor="cv" className="block text-sm font-medium">
            Candidate CV
          </label>
          <input
            id="cv"
            name="cv"
            type="file"
            accept="application/pdf"
            className="mt-2 block w-full cursor-pointer rounded-md border border-slate-300 p-2 text-sm file:mr-4 file:rounded file:border-0 file:bg-slate-100 file:px-3 file:py-1.5 file:text-slate-700 hover:file:bg-slate-200"
          />
          <p className="mt-1 text-xs text-slate-500">
            PDF only, up to 5 MB. A scanned CV will not work, because there is no
            text in it to read.
          </p>
        </div>

        <div>
          <label htmlFor="jobRole" className="block text-sm font-medium">
            Job role
          </label>
          <input
            id="jobRole"
            name="jobRole"
            type="text"
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
            defaultValue={8}
            className="mt-2 block w-24 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
          />
        </div>

        <button
          type="submit"
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
        >
          Generate questions
        </button>
      </form>
    </div>
  );
}
