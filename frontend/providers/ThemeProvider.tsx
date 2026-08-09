"use client";

import { createContext, useCallback, useState, type ReactNode } from "react";

import { applyTheme, getStoredTheme, storeTheme, type Theme } from "@/lib/theme";

export type ThemeContextValue = {
  theme: Theme;
  toggleTheme: () => void;
};

export const ThemeContext = createContext<ThemeContextValue>({
  theme: "light",
  toggleTheme: () => {},
});

export function ThemeProvider({ children }: { children: ReactNode }) {
  // The no-flash inline script in the root layout already applied the
  // `dark` class to <html> before hydration; this lazy initializer just
  // reads localStorage once to seed matching React state (SSR sees no
  // `window` and falls back to "light", same as the script's own default).
  const [theme, setTheme] = useState<Theme>(() => getStoredTheme() ?? "light");

  const toggleTheme = useCallback(() => {
    setTheme((current) => {
      const next: Theme = current === "dark" ? "light" : "dark";
      storeTheme(next);
      applyTheme(next);
      return next;
    });
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
