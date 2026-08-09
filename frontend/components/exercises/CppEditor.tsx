"use client";

import { useEffect, useRef, type KeyboardEvent, type UIEvent } from "react";

import { highlightCode, TOKEN_KIND_CLASS } from "@/lib/cpp-highlight";

export const CPP_STARTER_TEMPLATE = `#include <iostream>
using namespace std;

int main() {

    return 0;
}
`;

/**
 * A small, dependency-free C++ editor: a transparent <textarea> (for real
 * caret/selection/keyboard behavior) layered over a <pre> that renders the
 * same text through the existing highlightCode tokenizer, plus a
 * synced-scroll line-number gutter. Chosen over Monaco to keep this
 * lightweight and avoid Monaco's SSR/worker wiring cost in Next.js for a
 * single-language editor — see FRONTEND_HANDOFF follow-up decision log.
 */
export function CppEditor({
  value,
  onChange,
  disabled = false,
  className,
}: {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  className?: string;
}) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const preRef = useRef<HTMLPreElement>(null);
  const gutterRef = useRef<HTMLDivElement>(null);
  const pendingSelection = useRef<number | null>(null);

  useEffect(() => {
    if (pendingSelection.current !== null && textareaRef.current) {
      const pos = pendingSelection.current;
      textareaRef.current.selectionStart = pos;
      textareaRef.current.selectionEnd = pos;
      pendingSelection.current = null;
    }
  }, [value]);

  const lines = highlightCode(value);
  const lineCount = Math.max(lines.length, 1);

  const syncScroll = (event: UIEvent<HTMLTextAreaElement>) => {
    const { scrollTop, scrollLeft } = event.currentTarget;
    if (preRef.current) {
      preRef.current.scrollTop = scrollTop;
      preRef.current.scrollLeft = scrollLeft;
    }
    if (gutterRef.current) {
      gutterRef.current.scrollTop = scrollTop;
    }
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key !== "Tab") return;
    event.preventDefault();
    const target = event.currentTarget;
    const start = target.selectionStart;
    const end = target.selectionEnd;
    const nextValue = `${value.slice(0, start)}  ${value.slice(end)}`;
    pendingSelection.current = start + 2;
    onChange(nextValue);
  };

  const sharedTextClasses =
    "font-mono text-[13px] leading-[1.65] whitespace-pre";

  return (
    <div
      className={`flex overflow-hidden rounded-lg border border-[var(--color-border)] bg-[var(--color-code-bg)] ${className ?? ""}`}
    >
      <div
        ref={gutterRef}
        aria-hidden
        className={`select-none overflow-hidden py-3 pr-2.5 pl-3.5 text-right text-[var(--color-text-secondary)] ${sharedTextClasses}`}
      >
        {Array.from({ length: lineCount }, (_, i) => (
          <div key={i}>{i + 1}</div>
        ))}
      </div>
      <div className="relative min-h-[280px] flex-1">
        <pre
          ref={preRef}
          aria-hidden
          className={`pointer-events-none absolute inset-0 m-0 overflow-auto py-3 pr-3.5 ${sharedTextClasses}`}
        >
          <code>
            {lines.map((tokens, lineIndex) => (
              <div key={lineIndex}>
                {tokens.length === 0
                  ? " "
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
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onScroll={syncScroll}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          spellCheck={false}
          autoCapitalize="off"
          autoCorrect="off"
          aria-label="Editor de cod C++"
          className={`absolute inset-0 h-full w-full resize-none overflow-auto py-3 pr-3.5 text-transparent caret-[var(--color-text)] outline-none disabled:cursor-not-allowed ${sharedTextClasses}`}
        />
      </div>
    </div>
  );
}
