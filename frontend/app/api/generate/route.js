import { callBackend } from "../../lib/backend";

// The slow one. Two LLM calls happen behind this, so it takes around 45
// seconds before anything comes back.
export async function POST(request) {
  const payload = await request.json();

  return callBackend("/generate-questions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
