import { type FirebaseApp, getApps, initializeApp } from "firebase/app";
import { type Auth, getAuth } from "firebase/auth";

function firebaseConfig() {
  return {
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
    messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  };
}

function createFirebaseApp(): FirebaseApp {
  const existing = getApps();
  if (existing.length > 0) {
    return existing[0]!;
  }
  return initializeApp(firebaseConfig());
}

// Browser-only singleton. Firebase Auth's JS SDK requires `window`, so this
// module must never be imported from a server component.
export const firebaseApp: FirebaseApp = createFirebaseApp();
export const auth: Auth = getAuth(firebaseApp);
