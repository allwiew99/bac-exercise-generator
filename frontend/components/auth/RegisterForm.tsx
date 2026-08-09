"use client";

import { createUserWithEmailAndPassword } from "firebase/auth";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";

import { GoogleSignInButton } from "@/components/auth/GoogleSignInButton";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";
import { auth } from "@/lib/firebase";
import { mapFirebaseAuthError } from "@/lib/firebase-errors";

export function RegisterForm() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!authLoading && user) {
      router.replace("/dashboard");
    }
  }, [authLoading, user, router]);

  const goToDashboard = () => router.push("/dashboard");

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!email || !password) {
      setError("Completați toate câmpurile.");
      return;
    }
    if (password.length < 8) {
      setError("Parola trebuie să aibă minim 8 caractere.");
      return;
    }
    if (password !== confirm) {
      setError("Parolele nu coincid.");
      return;
    }
    setError("");
    setBusy(true);
    try {
      await createUserWithEmailAndPassword(auth, email, password);
      goToDashboard();
    } catch (err) {
      setError(mapFirebaseAuthError(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="mx-auto max-w-[400px] px-6 py-20">
      <h1 className="mb-1.5 font-display text-[26px] font-semibold">
        Creează cont
      </h1>
      <p className="mb-7 text-sm text-[var(--color-text-secondary)]">
        Creează-ți un cont gratuit pentru a genera exerciții.
      </p>

      {error ? (
        <div className="mb-4.5 rounded-lg bg-[var(--color-danger-bg)] px-3.5 py-3 text-[13px] text-[var(--color-danger)]">
          {error}
        </div>
      ) : null}

      <form onSubmit={handleSubmit} className="flex flex-col gap-3.5">
        <div>
          <label className="mb-1.5 block text-[13px] font-semibold">
            Email
          </label>
          <Input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="nume@exemplu.ro"
            autoComplete="email"
          />
        </div>
        <div>
          <label className="mb-1.5 block text-[13px] font-semibold">
            Parolă
          </label>
          <Input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="minim 8 caractere"
            autoComplete="new-password"
          />
        </div>
        <div>
          <label className="mb-1.5 block text-[13px] font-semibold">
            Confirmă parola
          </label>
          <Input
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder="••••••••"
            autoComplete="new-password"
          />
        </div>
        <Button type="submit" disabled={busy} className="mt-1.5 w-full">
          {busy ? "Se creează contul..." : "Creează cont"}
        </Button>

        <div className="my-1.5 flex items-center gap-2.5">
          <div className="h-px flex-1 bg-[var(--color-border)]" />
          <span className="text-xs text-[var(--color-text-secondary)]">
            sau
          </span>
          <div className="h-px flex-1 bg-[var(--color-border)]" />
        </div>

        <GoogleSignInButton
          onSuccess={goToDashboard}
          onError={(message) => {
            setError(message);
          }}
        />
      </form>

      <p className="mt-6 text-center text-sm text-[var(--color-text-secondary)]">
        Ai deja cont? <Link href="/login">Autentifică-te</Link>
      </p>
    </section>
  );
}
