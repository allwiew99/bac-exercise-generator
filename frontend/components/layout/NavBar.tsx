"use client";

import { signOut } from "firebase/auth";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { useAuth } from "@/hooks/useAuth";
import { auth } from "@/lib/firebase";
import { cn } from "@/lib/cn";

export function NavBar() {
  const { user, loading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = async () => {
    await signOut(auth);
    router.push("/");
  };

  return (
    <header className="sticky top-0 z-20 border-b border-[var(--color-border)] bg-[var(--color-bg)]">
      <div className="mx-auto flex max-w-[1120px] items-center justify-between gap-4 px-6 py-4.5">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="flex h-7.5 w-7.5 items-center justify-center rounded-[7px] bg-[var(--color-primary)] font-display text-[15px] font-bold text-white">
            B
          </span>
          <span className="font-display text-base font-semibold tracking-tight text-[var(--color-text)]">
            Bac Exercise Generator
          </span>
        </Link>

        {!loading && user ? (
          <nav className="flex items-center gap-6">
            <Link
              href="/dashboard"
              className={cn(
                "text-sm font-semibold no-underline",
                pathname === "/dashboard"
                  ? "text-[var(--color-primary)]"
                  : "text-[var(--color-text)]",
              )}
            >
              Panou
            </Link>
            <Link
              href="/exercises"
              className={cn(
                "text-sm font-semibold no-underline",
                pathname?.startsWith("/exercises")
                  ? "text-[var(--color-primary)]"
                  : "text-[var(--color-text)]",
              )}
            >
              Exercițiile mele
            </Link>
            <ThemeToggle />
            <div className="h-5.5 w-px bg-[var(--color-border)]" />
            <span className="text-[13px] text-[var(--color-text-secondary)]">
              {user.email}
            </span>
            <button
              type="button"
              onClick={handleLogout}
              className="bg-transparent text-sm font-semibold text-[var(--color-text-secondary)]"
            >
              Ieșire
            </button>
          </nav>
        ) : null}

        {!loading && !user ? (
          <nav className="flex items-center gap-5">
            <ThemeToggle />
            <Link
              href="/login"
              className="text-sm font-semibold text-[var(--color-text)] no-underline"
            >
              Autentificare
            </Link>
            <Link
              href="/register"
              className="rounded-lg bg-[var(--color-primary)] px-4.5 py-2.5 text-sm font-semibold text-white no-underline hover:no-underline"
            >
              Înregistrare
            </Link>
          </nav>
        ) : null}
      </div>
    </header>
  );
}
