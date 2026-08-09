import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import type { Difficulty } from "@/schemas/exercise";

export type DifficultyFilter = Difficulty | "all";

export function ExerciseFilters({
  topic,
  onTopicChange,
  difficulty,
  onDifficultyChange,
}: {
  topic: string;
  onTopicChange: (value: string) => void;
  difficulty: DifficultyFilter;
  onDifficultyChange: (value: DifficultyFilter) => void;
}) {
  return (
    <div className="mb-6 flex flex-wrap gap-3">
      <Input
        type="text"
        value={topic}
        onChange={(e) => onTopicChange(e.target.value)}
        placeholder="Caută după subiect..."
        className="w-[260px]"
      />
      <Select
        value={difficulty}
        onChange={(e) => onDifficultyChange(e.target.value as DifficultyFilter)}
        className="w-[180px]"
      >
        <option value="all">Toate dificultățile</option>
        <option value="easy">Ușor</option>
        <option value="medium">Mediu</option>
        <option value="hard">Dificil</option>
      </Select>
    </div>
  );
}
