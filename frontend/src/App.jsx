import { useState } from "react";
import "./App.css";
import UrlForm from "./components/UrlForm";
import ResultsTabs from "./components/ResultsTabs";
import { summarizeVideo } from "./api";

export default function App() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  async function handleSubmit() {
    setLoading(true);
    setError(null);
    try {
      const data = await summarizeVideo(url.trim());
      setResult(data);
    } catch (err) {
      setError(err.message);
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>VidBrief</h1>
        <p className="tagline">Turn any YouTube video into a summary, notes, quiz &amp; flashcards.</p>
      </header>

      <UrlForm url={url} onUrlChange={setUrl} onSubmit={handleSubmit} loading={loading} />

      {loading && (
        <div className="status-message loading-message">
          <span className="spinner" aria-hidden="true" />
          Fetching transcript and generating your study pack…
        </div>
      )}

      {error && !loading && (
        <div className="status-message error-message" role="alert">
          {error}
        </div>
      )}

      {result && !loading && !error && (
        <ResultsTabs key={result.video_id} result={result} />
      )}
    </div>
  );
}
