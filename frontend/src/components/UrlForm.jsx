export default function UrlForm({ url, onUrlChange, onSubmit, loading }) {
  function handleSubmit(e) {
    e.preventDefault();
    if (!loading) onSubmit();
  }

  return (
    <form className="url-form" onSubmit={handleSubmit}>
      <input
        type="text"
        className="url-input"
        placeholder="Paste a YouTube video URL…"
        value={url}
        onChange={(e) => onUrlChange(e.target.value)}
        disabled={loading}
        aria-label="YouTube video URL"
      />
      <button type="submit" className="submit-btn" disabled={loading || !url.trim()}>
        {loading ? "Summarizing…" : "Summarize"}
      </button>
    </form>
  );
}
