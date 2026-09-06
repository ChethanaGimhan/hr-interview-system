// One place that knows where FastAPI is and how to authenticate with it.
//
// This file only ever runs on the server. The key it reads is never sent to
// the browser and never ends up in the JavaScript bundle.

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000";

// The low level call. Pages use this directly, because a page that renders on
// the server can talk to the backend itself without going through a route.
export function backendFetch(path, options = {}) {
  return fetch(`${BACKEND_URL}${path}`, {
    ...options,
    // Never reuse a cached answer. The list of questionnaires changes every
    // time somebody generates one.
    cache: "no-store",
    headers: {
      ...options.headers,
      "x-api-key": process.env.INTERNAL_API_KEY || "",
    },
  });
}

// The wrapper the route handlers use, so anything the browser calls gets its
// errors back in the same shape.
export async function callBackend(path, options = {}) {
  let response;

  try {
    response = await backendFetch(path, options);
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
    // Not JSON at all. When that happens the reply came from something sitting
    // in front of the backend rather than from the backend itself, usually a
    // proxy error page, and putting a whole HTML document on the screen helps
    // nobody. Keep the real thing in the log and send back one short line.
    console.error(
      `Backend replied to ${path} with status ${response.status} and no JSON:`,
      text.slice(0, 500),
    );
    return Response.json(
      { detail: `The backend did not answer properly (status ${response.status})` },
      { status: response.status === 200 ? 502 : response.status },
    );
  }
}
