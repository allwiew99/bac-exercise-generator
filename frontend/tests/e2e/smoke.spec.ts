import { expect, test } from "@playwright/test";

import { mockFirebaseAuth } from "./mock-firebase";

test("login -> generate -> open exercise -> submit -> reveal solution -> history", async ({
  page,
}) => {
  await mockFirebaseAuth(page);

  await page.goto("/login");
  await page.getByPlaceholder("nume@exemplu.ro").fill("student@exemplu.ro");
  await page.getByPlaceholder("••••••••").fill("parola-de-test");
  await page.getByRole("button", { name: "Autentificare" }).click();

  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(
    page.getByRole("heading", { name: "Generează un exercițiu" }),
  ).toBeVisible();

  await page
    .getByPlaceholder("ex: vectori, recursivitate, matrice...")
    .fill("vectori");
  await page.getByRole("button", { name: "Generează exercițiul" }).click();

  await expect(
    page.getByText("Generăm și validăm exercițiul..."),
  ).toBeVisible();

  // Preferred production flow: the backend returns a persisted id and the
  // student lands directly on the working page for that exercise.
  await expect(page).toHaveURL(/\/exercises\/\d+$/, { timeout: 15_000 });

  // Before any submission: statement + editor are visible, the official
  // solution/explanation are not.
  await expect(page.getByText("vectori").first()).toBeVisible();
  await expect(page.getByText("Rezolvarea ta")).toBeVisible();
  await expect(page.getByText("Soluție C++")).not.toBeVisible();

  const editor = page.getByLabel("Editor de cod C++");
  await editor.fill(
    "#include <iostream>\nusing namespace std;\n\nint main() {\n    cout << 42;\n    return 0;\n}\n",
  );
  await page.getByRole("button", { name: "Verifică soluția" }).click();

  await expect(page.getByText(/^Scor: \d+\/100$/)).toBeVisible({
    timeout: 10_000,
  });
  await expect(page.getByText(/teste trecute/)).toBeVisible();

  // Official solution is only offered post-submission, and only appears
  // after the explicit reveal click.
  await expect(page.getByText("Soluție C++")).not.toBeVisible();
  await page
    .getByRole("button", { name: /Vezi soluția oficială/ })
    .click();
  await expect(page.getByText("Soluție C++")).toBeVisible();

  await page.goto("/exercises");
  await expect(
    page.getByRole("heading", { name: "Exercițiile mele" }),
  ).toBeVisible();
  await expect(page.getByText("vectori").first()).toBeVisible();
});
