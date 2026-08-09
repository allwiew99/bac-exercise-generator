import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { AuthContext } from "@/providers/AuthProvider";

const replace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
  usePathname: () => "/dashboard",
}));

// AuthProvider (imported transitively via AuthContext) pulls in
// lib/firebase, which initializes the real Firebase SDK on import — stub
// it so this component test doesn't need real Firebase env vars.
vi.mock("@/lib/firebase", () => ({
  auth: { currentUser: null },
}));

function renderWithAuth(value: { user: unknown; loading: boolean }) {
  return render(
    <AuthContext.Provider value={value as never}>
      <ProtectedRoute>
        <div>protected content</div>
      </ProtectedRoute>
    </AuthContext.Provider>,
  );
}

describe("ProtectedRoute", () => {
  it("renders nothing while auth state is still loading", () => {
    renderWithAuth({ user: null, loading: true });
    expect(screen.queryByText("protected content")).not.toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });

  it("redirects to /login with a next param when unauthenticated", () => {
    renderWithAuth({ user: null, loading: false });
    expect(screen.queryByText("protected content")).not.toBeInTheDocument();
    expect(replace).toHaveBeenCalledWith("/login?next=%2Fdashboard");
  });

  it("renders children once authenticated", () => {
    renderWithAuth({ user: { uid: "1" }, loading: false });
    expect(screen.getByText("protected content")).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });
});
