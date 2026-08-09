import type { TestCase } from "@/schemas/exercise";

export function TestCasesList({
  testCases,
  title = "Cazuri de test",
}: {
  testCases: TestCase[];
  title?: string;
}) {
  return (
    <div className="rounded-xl border border-[var(--color-border)] p-5">
      <div className="mb-3.5 text-[15px] font-semibold">{title}</div>
      <div className="flex flex-col gap-2.5">
        {testCases.map((testCase, index) => (
          <div key={index} className="grid grid-cols-2 gap-3">
            <div>
              <div className="mb-1.5 text-[11.5px] font-bold tracking-wide text-[var(--color-text-secondary)] uppercase">
                Input
              </div>
              <pre className="m-0 overflow-x-auto rounded-lg bg-[var(--color-code-bg)] px-3 py-2.5 font-mono text-[12.5px] break-words whitespace-pre-wrap">
                {testCase.input}
              </pre>
            </div>
            <div>
              <div className="mb-1.5 text-[11.5px] font-bold tracking-wide text-[var(--color-text-secondary)] uppercase">
                Rezultat așteptat
              </div>
              <pre className="m-0 overflow-x-auto rounded-lg bg-[var(--color-code-bg)] px-3 py-2.5 font-mono text-[12.5px] break-words whitespace-pre-wrap">
                {testCase.expected_output}
              </pre>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
