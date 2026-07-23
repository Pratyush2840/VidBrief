const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function summarizeVideo(youtubeUrl) {
  let res;
  try {
    res = await fetch(`${API_BASE_URL}/api/summarize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ youtube_url: youtubeUrl }),
    });
  } catch {
    throw new Error("Could not reach the server. Is the backend running?");
  }

  const data = await res.json().catch(() => null);

  if (!res.ok) {
    const message = data && data.detail ? data.detail : `Request failed (${res.status}).`;
    throw new Error(message);
  }

  return data;
}
