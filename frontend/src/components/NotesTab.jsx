export default function NotesTab({ notes }) {
  return (
    <div className="notes-tab">
      {notes.map((section, i) => (
        <div className="note-section" key={i}>
          <h3 className="note-heading">{section.heading}</h3>
          <ul className="note-points">
            {section.points.map((point, j) => (
              <li key={j}>{point}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
