import { cn } from "@/lib/cn";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-[var(--color-border)]",
        className,
      )}
    />
  );
}

export function ExerciseCardSkeleton() {
  return (
    <div className="flex items-center justify-between gap-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-3 w-24" />
      </div>
      <Skeleton className="h-6 w-16 rounded-full" />
    </div>
  );
}

export function ExerciseListSkeleton() {
  return (
    <div className="flex flex-col gap-2.5">
      <ExerciseCardSkeleton />
      <ExerciseCardSkeleton />
      <ExerciseCardSkeleton />
    </div>
  );
}

export function ExerciseDetailSkeleton() {
  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Skeleton className="h-6 w-24 rounded-full" />
        <Skeleton className="h-6 w-16 rounded-full" />
      </div>
      <Skeleton className="h-8 w-3/4" />
      <Skeleton className="h-8 w-1/2" />
      <Skeleton className="h-40 w-full rounded-xl" />
      <Skeleton className="h-24 w-full rounded-xl" />
    </div>
  );
}
