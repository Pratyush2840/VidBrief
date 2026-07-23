import { useState } from "react";

export default function QuizTab({ quiz }) {
  const [answers, setAnswers] = useState(() => Array(quiz.length).fill(null));

  function selectOption(questionIndex, optionIndex) {
    if (answers[questionIndex] !== null) return;
    setAnswers((prev) => {
      const next = [...prev];
      next[questionIndex] = optionIndex;
      return next;
    });
  }

  const answeredCount = answers.filter((a) => a !== null).length;
  const correctCount = quiz.filter(
    (q, i) => answers[i] === q.correct_index
  ).length;

  return (
    <div className="quiz-tab">
      <div className="quiz-score">
        Score: {correctCount} / {quiz.length}
        {answeredCount < quiz.length && (
          <span className="quiz-progress"> · {answeredCount}/{quiz.length} answered</span>
        )}
      </div>

      {quiz.map((q, qi) => {
        const selected = answers[qi];
        const isAnswered = selected !== null;

        return (
          <div className="quiz-question" key={qi}>
            <p className="quiz-question-text">
              {qi + 1}. {q.question}
            </p>
            <div className="quiz-options">
              {q.options.map((option, oi) => {
                let optionClass = "quiz-option";
                if (isAnswered) {
                  if (oi === q.correct_index) {
                    optionClass += " correct";
                  } else if (oi === selected) {
                    optionClass += " incorrect";
                  }
                }
                return (
                  <button
                    type="button"
                    key={oi}
                    className={optionClass}
                    onClick={() => selectOption(qi, oi)}
                    disabled={isAnswered}
                  >
                    {option}
                  </button>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
