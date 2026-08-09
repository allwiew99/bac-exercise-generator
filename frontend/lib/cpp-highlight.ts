const KEYWORDS = new Set([
  "int", "float", "double", "char", "bool", "void", "if", "else", "for",
  "while", "do", "return", "include", "using", "namespace", "std", "const",
  "string", "vector", "struct", "class", "public", "private", "static",
  "break", "continue", "switch", "case", "default", "true", "false", "long",
  "unsigned", "auto", "getline",
]);

export type TokenKind =
  | "comment"
  | "string"
  | "preproc"
  | "number"
  | "keyword"
  | "punct"
  | "text";

export type Token = { text: string; kind: TokenKind };

const TOKEN_RE =
  /(\/\/.*$)|("(?:[^"\\]|\\.)*")|('(?:[^'\\]|\\.)*')|(#\w+)|(\b\d+\.?\d*\b)|([A-Za-z_]\w*)|(\s+)|([^\sA-Za-z_0-9]+)/g;

/** Tokenizes one line of C++ source for syntax highlighting. */
export function highlightLine(line: string): Token[] {
  const tokens: Token[] = [];
  const re = new RegExp(TOKEN_RE.source, "g");
  let match: RegExpExecArray | null;

  while ((match = re.exec(line)) !== null) {
    const [full, comment, str, chr, preproc, num, word, , punct] = match;
    let kind: TokenKind = "text";
    if (comment) kind = "comment";
    else if (str || chr) kind = "string";
    else if (preproc) kind = "preproc";
    else if (num) kind = "number";
    else if (word && KEYWORDS.has(word)) kind = "keyword";
    else if (punct) kind = "punct";
    tokens.push({ text: full, kind });

    if (match.index === re.lastIndex) {
      re.lastIndex += 1;
    }
  }

  return tokens;
}

export function highlightCode(code: string): Token[][] {
  return code.split("\n").map(highlightLine);
}

/** Shared color mapping for both the read-only CodeBlock and the writable
 * CppEditor, so highlighted solution code and the editor look consistent. */
export const TOKEN_KIND_CLASS: Record<TokenKind, string> = {
  comment: "text-[var(--color-text-secondary)]",
  string: "text-[var(--color-success)]",
  preproc: "text-[var(--color-primary)]",
  number: "text-[var(--color-warning)]",
  keyword: "text-[var(--color-primary)]",
  punct: "text-[var(--color-text-secondary)]",
  text: "text-[var(--color-text)]",
};
