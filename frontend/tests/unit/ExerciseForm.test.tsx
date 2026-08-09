import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ExerciseForm } from "@/components/exercises/ExerciseForm";

describe("ExerciseForm", () => {
  it("blocks submission and shows an error when the topic is empty", async () => {
    const onSubmit = vi.fn();
    render(<ExerciseForm busy={false} onSubmit={onSubmit} />);

    await userEvent.click(
      screen.getByRole("button", { name: "Generează exercițiul" }),
    );

    expect(
      await screen.findByText("Te rugăm să introduci un subiect."),
    ).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits the trimmed topic and selected difficulty when valid", async () => {
    const onSubmit = vi.fn();
    render(<ExerciseForm busy={false} onSubmit={onSubmit} />);

    await userEvent.type(
      screen.getByPlaceholderText("ex: vectori, recursivitate, matrice..."),
      "  vectori  ",
    );
    await userEvent.click(screen.getByRole("button", { name: "Dificil" }));
    await userEvent.click(
      screen.getByRole("button", { name: "Generează exercițiul" }),
    );

    expect(onSubmit).toHaveBeenCalledWith({
      topic: "vectori",
      difficulty: "hard",
    });
  });

  it("disables the submit button while busy", () => {
    render(<ExerciseForm busy onSubmit={vi.fn()} />);
    expect(
      screen.getByRole("button", { name: "Generează exercițiul" }),
    ).toBeDisabled();
  });

  it("shows a server-provided form error banner", () => {
    render(
      <ExerciseForm
        busy={false}
        onSubmit={vi.fn()}
        formError="Cererea nu a putut fi procesată. Verifică subiectul introdus."
      />,
    );
    expect(
      screen.getByText(
        "Cererea nu a putut fi procesată. Verifică subiectul introdus.",
      ),
    ).toBeInTheDocument();
  });
});
