// One place that knows how to call FastAPI. Every route handler goes through
// here, so the API key is attached in a single spot and errors come back in the
// same shape no matter which endpoint was called.
//
// This file only ever runs on the server. The key it reads is never sent to the
// browser and never ends up in the JavaScript bundle.

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000";

export async function callBackend(path, options = {}) {
  let response;

  try {
    response = await fetch(`${BACKEND_URL}${path}`, {
      ...options,
      headers: {
        ...options.headers,
        "x-api-key": process.env.INTERNAL_API_KEY || "",
      },
    });
  } catch (error) {
    // Thrown when the backend is not running at all, or the hostname does not
    // resolve. The user gets a plain message, the reason goes to the log.
    console.error(`Could not reach the backend at ${BACKEND_URL}${path}:`, error.message);
    return Response.json({ detail: "The backend is not reachable" }, { status: 502 });
  }

  // FastAPI answers with JSON, but an unhandled error comes back as plain text,
  // so read the body as text first and only then try to parse it. Calling
  // .json() straight away would throw and hide the real status code.
  const text = await response.text();

  try {
    return Response.json(JSON.parse(text), { status: response.status });
  } catch {
    return Response.json(
      { detail: text || "The backend sent an empty reply" },
      { status: response.status },
    );
  }
}
