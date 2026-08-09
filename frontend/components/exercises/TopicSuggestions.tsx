const TOPICS = [
  "vectori",
  "recursivitate",
  "matrice",
  "șiruri de caractere",
  "sortare",
  "grafuri",
];

export function TopicSuggestions({
  onPick,
}: {
  onPick: (topic: string) => void;
}) {
  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {TOPICS.map((topic) => (
        <button
          key={topic}
          type="button"
          onClick={() => onPick(topic)}
          className="rounded-2xl bg-[var(--color-accent-bg)] px-3 py-1.5 text-[12.5px] font-semibold text-[var(--color-primary)]"
        >
          {topic}
        </button>
      ))}
    </div>
  );
}
