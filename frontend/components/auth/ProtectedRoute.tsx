"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { useAuth } from "@/hooks/useAuth";

/**
 * Client-side UX gating only. The backend verifying the Firebase ID token
 * and enforcing per-user ownership is the real security boundary — this
 * component just avoids flashing protected UI to a signed-out visitor.
 */
export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !user) {
      const next = encodeURIComponent(pathname ?? "/dashboard");
      router.replace(`/login?next=${next}`);
    }
  }, [loading, user, pathname, router]);

  if (loading || !user) {
    return null;
  }

  return <>{children}</>;
}
