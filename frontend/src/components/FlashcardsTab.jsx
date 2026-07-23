import { useState } from "react";

function Flashcard({ front, back }) {
  const [flipped, setFlipped] = useState(false);

  return (
    <button
      type="button"
      className={`flashcard ${flipped ? "flipped" : ""}`}
      onClick={() => setFlipped((f) => !f)}
      aria-label="Flip flashcard"
    >
      <div className="flashcard-inner">
        <div className="flashcard-face flashcard-front">{front}</div>
        <div className="flashcard-face flashcard-back">{back}</div>
      </div>
    </button>
  );
}

export default function FlashcardsTab({ flashcards }) {
  return (
    <div className="flashcards-tab">
      {flashcards.map((card, i) => (
        <Flashcard key={i} front={card.front} back={card.back} />
      ))}
    </div>
  );
}
