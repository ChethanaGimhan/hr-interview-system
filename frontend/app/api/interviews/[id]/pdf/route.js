import { backendFetch } from "@/app/lib/backend";

// The browser cannot ask FastAPI for the PDF itself, because it has no API
// key, so the file comes through here instead.
//
// callBackend is no use for this one: it parses the reply as JSON, and this
// reply is a PDF. The body is passed straight through untouched.
export async function GET(request, { params }) {
  const { id } = await params;

  let response;
  try {
    response = await backendFetch(`/interviews/${encodeURIComponent(id)}/pdf`);
  } catch (error) {
    console.error("Could not reach the backend for a PDF:", error.message);
    return Response.json({ detail: "The backend is not reachable" }, { status: 502 });
  }

  if (!response.ok) {
    return Response.json(
      { detail: "That questionnaire could not be turned into a PDF" },
      { status: response.status },
    );
  }

  return new Response(response.body, {
    headers: {
      "Content-Type": "application/pdf",
      // The backend already worked out a safe file name, so reuse it.
      "Content-Disposition": response.headers.get("content-disposition") || "attachment",
    },
  });
}
