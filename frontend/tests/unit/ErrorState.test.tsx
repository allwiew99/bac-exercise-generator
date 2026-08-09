import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ErrorState } from "@/components/ui/ErrorState";

const push = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

describe("ErrorState", () => {
  it("shows the 429 rate-limit copy and returns to the dashboard, not an auto-retry", async () => {
    render(
      <ErrorState error={{ status: 429, code: "rate_limited", detail: "" }} />,
    );

    expect(screen.getByText("Limită atinsă")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Ai atins limita de generări. Te rugăm să încerci din nou mai târziu.",
      ),
    ).toBeInTheDocument();

    await userEvent.click(
      screen.getByRole("button", { name: "Înapoi la panou" }),
    );
    expect(push).toHaveBeenCalledWith("/dashboard");
  });

  it("shows the 403 copy with a link back to the history list", () => {
    render(
      <ErrorState error={{ status: 403, code: "forbidden", detail: "" }} />,
    );
    expect(screen.getByText("Acces interzis")).toBeInTheDocument();
    expect(screen.getByText("Nu ai acces la acest exercițiu.")).toBeInTheDocument();
  });

  it("shows the 404 copy for a missing exercise", () => {
    render(
      <ErrorState error={{ status: 404, code: "not_found", detail: "" }} />,
    );
    expect(screen.getByText("Exercițiu negăsit")).toBeInTheDocument();
  });

  it("calls onRetry for a 500-class error instead of navigating", async () => {
    const onRetry = vi.fn();
    render(
      <ErrorState
        error={{ status: 500, code: "server_error", detail: "" }}
        onRetry={onRetry}
      />,
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Încearcă din nou" }),
    );
    expect(onRetry).toHaveBeenCalledTimes(1);
    expect(push).not.toHaveBeenCalled();
  });
});
