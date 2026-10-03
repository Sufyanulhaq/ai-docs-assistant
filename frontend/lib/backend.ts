export const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export function backendUnavailable() {
  return Response.json(
    { detail: "The assistant backend is not reachable. Is it running?" },
    { status: 502 },
  );
}
