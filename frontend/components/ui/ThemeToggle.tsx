"use client";

import { useTheme } from "@/hooks/useTheme";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      type="button"
      onClick={toggleTheme}
      title="Comută tema"
      aria-label="Comută tema"
      className="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--color-border)] text-[var(--color-text-secondary)]"
    >
      {theme === "dark" ? "☀" : "☾"}
    </button>
  );
}
