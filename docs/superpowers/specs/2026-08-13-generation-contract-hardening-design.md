# Generation Contract Hardening Design

## Objective

Make generated Bac Informatics exercises consistently executable under the
existing stdin/stdout C++ validation harness, reject overly derivative
statements through the existing repair loop, bound Gemini output size, and
validate the real Cloud Run sandbox without deploying a production revision.

The retrieval strategy remains unchanged: Vertex query embedding, Pinecone
metadata filtering with semantic fallback, Pinecone ordering, five context
chunks, reranking disabled, and RAG fail-open behavior.

## Confirmed root causes

### File exercises

The prompt requires a complete C++ solution but does not define the I/O
contract. Retrieved Bac references legitimately mention `bac.txt`; Gemini can
therefore generate `ifstream`, `freopen`, or named-file solutions. Both
`LocalCodeRunner` and `SandboxCodeRunner` provide test data only on stdin and
compare stdout, so file-opening programs cannot consume their tests.

### Subprogram exercises

The prompt allows Bac-style subprogram tasks but does not require the reference
solution to include an executable harness. Gemini produced only the requested
function. `CodeValidator` correctly compiles a translation unit as a complete
program, and the linker rejected the missing `main()` on all three retries.

### Novelty

The prompt's anti-copy instruction is advisory. `ExerciseService` currently
receives only rendered RAG context, so it cannot compare generated statements
with the source chunks. The E2E pseudocode case reached token Jaccard `0.7476`,
well above the highest accepted sample (`0.3659`).

### Gemini response length

`GenerateContentConfig.max_output_tokens` is unset. Gemini 2.5 Flash can emit up
to 65,536 output tokens. Successful E2E JSON payloads measured 513–1,661 tokens;
the failed matrices response grew to approximately 41,000 characters before
ending as truncated JSON.

## Generation contracts

### Universal executable solution contract

Every `ExerciseResponse.solution` is a complete C++17 program that:

- contains one `main()` entry point;
- reads all test input from standard input;
- writes only the requested answer to standard output;
- compiles and runs against every generated `ExerciseTestCase`.

The prompt states this contract for initial and repair generations.
`ExerciseValidator` performs deterministic preflight validation before invoking
the compiler:

- reject a missing `main()` with an actionable repair message;
- reject file APIs or named-file access with an actionable stdin/stdout message.

Compilation and test execution remain mandatory; the preflight rules do not
replace or weaken `CodeValidator`.

### File-topic contract

File processing remains a Bac topic, but the executable exercise models file
contents as an input stream. The statement may describe data that conceptually
comes from a file, but it must explicitly say those contents are supplied on
standard input. The reference solution must not use `ifstream`, `ofstream`,
`fstream`, `freopen`, `.open(...)`, or a hard-coded filename.

The validator applies this no-file-I/O rule to every generated reference
solution, giving all topics one runner-compatible contract and preventing an
incorrect topic label from bypassing the rule.

### Subprogram-topic contract

The student-facing statement may ask for a subprogram definition in normal
Bac style. The reference solution contains both:

- the requested function/subprogram; and
- a small `main()` harness that reads the function parameters from stdin,
  invokes the function, and prints its observable result or modified values.

Generated test cases target this complete program.

## RAG result and novelty flow

`RagContextProvider.get_context()` returns a `RagContext` value containing:

- `text`: rendered context passed to `PromptBuilder`;
- `chunks`: retrieved references in the exact order supplied to
  `ContextBuilder` before its top-five truncation.

Disabled or fail-open RAG returns an empty `RagContext`. This explicit value
avoids request-global mutable state and remains safe under concurrent requests.

`ExerciseService.generate()` uses `rag_context.text` for both initial and repair
prompts. After each valid JSON response and before C++ compilation, it calls an
`ExerciseNoveltyValidator` with the generated statement and retrieved chunks.
Suspicious similarity raises `ExerciseValidationError`, entering the existing
repair/retry loop. There is no second generation mechanism.

Thresholds live together in one immutable policy:

- normalized exact match; or
- token Jaccard greater than or equal to `0.60`; or
- five-token shingle containment greater than or equal to `0.60`.

Only statement similarity determines production rejection. Constants,
test-case overlap, and solution overlap remain evaluation/reporting diagnostics.
Logs include reference IDs and numeric similarity scores, never reference text.
An unexpected novelty-evaluator error logs a safe warning and returns success so
generation remains fail-open for this auxiliary guard.

## Gemini output bound

Add `gemini_max_output_tokens: int = 8192` to settings and pass it explicitly to
`GenerateContentConfig.max_output_tokens`.

The prompt also requests a Bac-sized response:

- concise, self-contained statement;
- explanation limited to the algorithm, correctness, and complexity;
- complete but compact C++17 solution;
- no repeated statement or reference content;
- total JSON response comfortably within 8,192 output tokens.

The 8,192-token ceiling is nearly five times the largest successful observed
payload while reducing the model ceiling by 87.5%. A truncated response remains
an `LLMResponseError` and uses the existing retry path.

## Isolated Cloud Run sandbox validation

Add a runnable module included in the normal image. It invokes the actual
`SandboxCodeRunner` and checks:

1. `/usr/local/gcp/bin/sandbox` exists;
2. a complete C++17 program compiles and reads stdin/writes stdout correctly;
3. the runner-created host workspace is mounted at `/workspace` by the sandbox
   command (exercised by the successful run path);
4. a program returning nonzero is rejected;
5. an infinite loop is terminated by the two-second execution timeout.

Build a uniquely tagged image with Cloud Build and deploy an isolated Cloud Run
Job named `bac-rag-sandbox-validation` with `--sandbox-launcher`, no secrets, no
database, no public endpoint, no production traffic, no retries, and a bounded
task timeout. Execute it once and retain its execution/log evidence. This is not
a production service revision or final deployment.

## E2E persistence isolation

No staging database secret exists. The E2E runner therefore uses the configured
database with a unique validation UID of the form
`__rag_e2e_validation__<UTC-run-id>`. Firebase UIDs cannot be chosen by normal
users, and repository list/get operations are scoped to the authenticated UID,
so these rows cannot appear in ordinary user flows.

The runner:

1. records every persisted exercise ID;
2. writes and validates the JSON report;
3. deletes rows only where `user_id` exactly equals that run's validation UID;
4. commits the deletion;
5. records inserted IDs, inserted count, deleted count, cleanup completion, and
   the deterministic cleanup SQL in the report;
6. verifies zero rows remain for that UID.

If report writing or cleanup fails, the console prints the exact UID and cleanup
SQL before exiting nonzero. No wildcard or broad deletion is used.

## E2E acceptance criteria

Run the same eight requests: pseudocode/medium, arrays/easy,
matrices/medium, files/hard, graphs/medium, number processing/easy,
subprograms/hard, and binary search/medium.

Acceptance requires:

- eight generated, validated, executable, and temporarily persisted exercises;
- five non-empty RAG context chunks per case;
- Pinecone order preserved;
- zero suspicious novelty results;
- reranker disabled and zero construction/Discovery Engine calls;
- fail-open generation succeeds with empty context;
- fail-closed propagates before Gemini generation;
- all validation rows deleted and verified absent;
- live Pinecone namespace remains exactly 317 vectors.

## Testing and safety

Unit tests cover prompt contracts, deterministic executable-contract checks,
centralized novelty thresholds, repair-loop integration, novelty fail-open,
Gemini token configuration, RAG context/reference propagation, persistence
cleanup, and sandbox validation outcomes with external boundaries mocked.

The full quality gate is `py_compile`, strict mypy, Ruff, focused tests, and the
complete pytest suite. Corpus contents, Pinecone vectors, reranker behavior,
deployment configuration, and the production Cloud Run service remain
unchanged.
