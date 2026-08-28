// Something cheap for the Kubernetes probes to call. It deliberately does not
// touch the backend: if the backend goes down, every frontend pod would fail
// this check at once and be pulled out of the service, turning one outage into
// two. The same reasoning as the /health endpoint on the backend.
export async function GET() {
  return Response.json({ status: "ok" });
}
