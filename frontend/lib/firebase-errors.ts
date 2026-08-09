import { FirebaseError } from "firebase/app";

const MESSAGES: Record<string, string> = {
  "auth/invalid-email": "Adresa de email nu este validă.",
  "auth/user-disabled": "Acest cont a fost dezactivat.",
  "auth/user-not-found": "Nu există niciun cont cu acest email.",
  "auth/wrong-password": "Parolă incorectă.",
  "auth/invalid-credential": "Email sau parolă incorectă.",
  "auth/email-already-in-use": "Există deja un cont cu acest email.",
  "auth/weak-password": "Parola trebuie să aibă minim 8 caractere.",
  "auth/too-many-requests":
    "Prea multe încercări. Te rugăm să încerci din nou mai târziu.",
  "auth/network-request-failed":
    "Nu am putut contacta serverul de autentificare. Verifică conexiunea la internet.",
  "auth/popup-closed-by-user": "Fereastra de autentificare a fost închisă.",
  "auth/cancelled-popup-request": "Fereastra de autentificare a fost închisă.",
};

const DEFAULT_MESSAGE = "Autentificarea a eșuat. Te rugăm să încerci din nou.";

export function mapFirebaseAuthError(error: unknown): string {
  if (error instanceof FirebaseError) {
    return MESSAGES[error.code] ?? DEFAULT_MESSAGE;
  }
  return DEFAULT_MESSAGE;
}
