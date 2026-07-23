import { useState } from "react";
import SummaryTab from "./SummaryTab";
import NotesTab from "./NotesTab";
import QuizTab from "./QuizTab";
import FlashcardsTab from "./FlashcardsTab";

const TABS = ["Summary", "Notes", "Quiz", "Flashcards"];

export default function ResultsTabs({ result }) {
  const [activeTab, setActiveTab] = useState(TABS[0]);

  return (
    <div className="results">
      <div className="tab-bar" role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab}
            type="button"
            role="tab"
            aria-selected={activeTab === tab}
            className={`tab-btn ${activeTab === tab ? "active" : ""}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="tab-panel">
        {activeTab === "Summary" && <SummaryTab summary={result.summary} />}
        {activeTab === "Notes" && <NotesTab notes={result.notes} />}
        {activeTab === "Quiz" && <QuizTab quiz={result.quiz} />}
        {activeTab === "Flashcards" && (
          <FlashcardsTab flashcards={result.flashcards} />
        )}
      </div>
    </div>
  );
}
