"use client";

import { useState } from "react";

import { highlightCode, TOKEN_KIND_CLASS } from "@/lib/cpp-highlight";

export function CodeBlock({ code }: { code: string }) {
  const [copyLabel, setCopyLabel] = useState("Copiază");
  const lines = highlightCode(code);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopyLabel("Copiat ✓");
      setTimeout(() => setCopyLabel("Copiază"), 1500);
    } catch {
      // Clipboard API unavailable (e.g. insecure context) — no-op.
    }
  };

  return (
    <div className="relative bg-[var(--color-code-bg)]">
      <button
        type="button"
        onClick={handleCopy}
        className="absolute top-3 right-3 z-10 rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1.5 text-xs font-semibold text-[var(--color-text)]"
      >
        {copyLabel}
      </button>
      <pre className="overflow-x-auto p-5 font-mono text-[13px] leading-[1.65]">
        <code>
          {lines.map((tokens, lineIndex) => (
            <div key={lineIndex}>
              {tokens.length === 0
                ? " "
                : tokens.map((token, tokenIndex) => (
                    <span
                      key={tokenIndex}
                      className={TOKEN_KIND_CLASS[token.kind]}
                    >
                      {token.text}
                    </span>
                  ))}
            </div>
          ))}
        </code>
      </pre>
    </div>
  );
}
