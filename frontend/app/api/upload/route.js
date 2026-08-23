import { callBackend } from "../backend";

// The browser posts the PDF here and this passes it on to FastAPI. The file is
// forwarded as it arrived, so the size limit and the %PDF- check on the backend
// are still the things that decide whether it is accepted.
export async function POST(request) {
  const formData = await request.formData();
  const file = formData.get("file");

  if (!file) {
    return Response.json({ detail: "No file was sent" }, { status: 400 });
  }

  const forwarded = new FormData();
  forwarded.append("file", file, file.name);

  // No Content-Type header here on purpose. fetch writes it itself, including
  // the random boundary string that separates the parts of the upload, and
  // setting it by hand would leave that boundary out and break the request.
  return callBackend("/upload-cv", { method: "POST", body: forwarded });
}
