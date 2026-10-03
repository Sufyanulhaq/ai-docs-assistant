import { BACKEND_URL, backendUnavailable } from "@/lib/backend";

export async function GET() {
  try {
    const upstream = await fetch(`${BACKEND_URL}/api/health`, { cache: "no-store" });
    return Response.json(await upstream.json(), { status: upstream.status });
  } catch {
    return backendUnavailable();
  }
}
