import { cn } from "@/lib/cn";
import { DIFFICULTY_LABEL } from "@/lib/difficulty";
import type { Difficulty } from "@/schemas/exercise";

const OPTIONS: Difficulty[] = ["easy", "medium", "hard"];

export function DifficultySelector({
  value,
  onChange,
}: {
  value: Difficulty;
  onChange: (value: Difficulty) => void;
}) {
  return (
    <div className="grid grid-cols-3 gap-2 rounded-[10px] border border-[var(--color-border)] bg-[var(--color-bg)] p-1.5">
      {OPTIONS.map((option) => {
        const active = value === option;
        return (
          <button
            key={option}
            type="button"
            onClick={() => onChange(option)}
            className={cn(
              "rounded-[7px] px-2.5 py-2.5 text-[13.5px] font-semibold",
              active
                ? "bg-[var(--color-surface)] text-[var(--color-primary)] shadow-sm"
                : "bg-transparent text-[var(--color-text-secondary)]",
            )}
          >
            {DIFFICULTY_LABEL[option]}
          </button>
        );
      })}
    </div>
  );
}
