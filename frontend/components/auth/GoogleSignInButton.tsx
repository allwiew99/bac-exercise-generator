"use client";

import { GoogleAuthProvider, signInWithPopup } from "firebase/auth";

import { mapFirebaseAuthError } from "@/lib/firebase-errors";
import { auth } from "@/lib/firebase";

export function GoogleSignInButton({
  onSuccess,
  onError,
}: {
  onSuccess: () => void;
  onError: (message: string) => void;
}) {
  const handleClick = async () => {
    try {
      await signInWithPopup(auth, new GoogleAuthProvider());
      onSuccess();
    } catch (error) {
      onError(mapFirebaseAuthError(error));
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      className="flex items-center justify-center gap-2.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-3.5 text-sm font-semibold text-[var(--color-text)]"
    >
      <span className="font-display font-bold text-[var(--color-primary)]">
        G
      </span>
      Continuă cu Google
    </button>
  );
}
