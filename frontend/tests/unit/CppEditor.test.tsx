import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import {
  CPP_STARTER_TEMPLATE,
  CppEditor,
} from "@/components/exercises/CppEditor";

describe("CPP_STARTER_TEMPLATE", () => {
  it("is a compilable-looking C++ skeleton with an empty main body", () => {
    expect(CPP_STARTER_TEMPLATE).toContain("#include <iostream>");
    expect(CPP_STARTER_TEMPLATE).toContain("int main()");
    expect(CPP_STARTER_TEMPLATE).toContain("return 0;");
  });
});

describe("CppEditor", () => {
  it("renders the given value and calls onChange as the student types", async () => {
    const onChange = vi.fn();
    render(<CppEditor value="int x;" onChange={onChange} />);

    const editor = screen.getByLabelText("Editor de cod C++");
    expect(editor).toHaveValue("int x;");

    await userEvent.type(editor, "y");
    expect(onChange).toHaveBeenCalled();
  });

  it("disables the textarea while a submission is pending", () => {
    render(<CppEditor value="int x;" onChange={vi.fn()} disabled />);
    expect(screen.getByLabelText("Editor de cod C++")).toBeDisabled();
  });

  it("renders one gutter line number per line of code", () => {
    const { container } = render(
      <CppEditor value={"line1\nline2\nline3"} onChange={vi.fn()} />,
    );
    const gutter = container.querySelector('[aria-hidden="true"]');
    expect(gutter?.textContent).toBe("123");
  });

  it("inserts two spaces and does not move focus when Tab is pressed", async () => {
    const onChange = vi.fn();
    render(<CppEditor value="abc" onChange={onChange} />);
    const editor = screen.getByLabelText("Editor de cod C++") as HTMLTextAreaElement;
    editor.focus();
    editor.setSelectionRange(3, 3);

    await userEvent.keyboard("{Tab}");

    expect(onChange).toHaveBeenCalledWith("abc  ");
  });
});
