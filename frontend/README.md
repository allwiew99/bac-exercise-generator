# Bac Exercise Generator — Frontend

Next.js (App Router) + TypeScript (strict) + Tailwind CSS v4 frontend for the
Bac Exercise Generator FastAPI backend.

**Product flow (v1.1):** a student picks a topic/difficulty, the backend
generates and validates an exercise, and the student sees only the
statement — never the official solution, explanation, or hidden test
cases. They write their own C++ solution in-browser, submit it for
grading, and only after that first submission can they reveal the official
solution/explanation.

## Stack

- Next.js 16 (App Router), TypeScript strict
- Tailwind CSS v4 (CSS-first config — theme tokens live in `app/globals.css`,
  no `tailwind.config.ts`; dark mode via `@custom-variant dark` + a `.dark`
  class on `<html>`)
- Firebase Web SDK (email/password + Google sign-in)
- TanStack Query (server state)
- Zod (request/response validation — also the compatibility boundary, see
  below)
- A small dependency-free C++ tokenizer (`lib/cpp-highlight.ts`), shared by
  the read-only solution `CodeBlock` and the writable `CppEditor` — avoids
  pulling in a full syntax-highlighter or Monaco for one language
- Vitest + React Testing Library (unit/component tests)
- Playwright (one smoke flow, Firebase and the backend both mocked)

## Getting started

```bash
npm install
cp .env.example .env.local   # fill in the values below
npm run dev
```

### Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | yes | FastAPI backend base URL. Only source of truth — never hardcoded in source. |
| `NEXT_PUBLIC_FIREBASE_API_KEY` | yes | Firebase Web SDK config (Console → Project settings → Web app). Public/browser-safe by Firebase's own design. |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | yes | " |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | yes | " |
| `NEXT_PUBLIC_FIREBASE_APP_ID` | yes | " |
| `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` | yes | " |
| `NEXT_PUBLIC_USE_MOCK_API` | no | `true` serves in-memory fixtures instead of calling the backend. Only takes effect when `NODE_ENV !== "production"` — cannot activate in a real deploy even if left `true` by mistake. |

All `NEXT_PUBLIC_*` values are inlined at build time, so each environment
(local/staging/prod) needs its own build (or runtime env injection,
depending on host).

### Firebase setup

1. Create (or reuse) a Firebase project.
2. Enable **Email/Password** and **Google** sign-in providers under
   Authentication → Sign-in method.
3. Register a Web app under Project settings → Your apps, copy the config
   values into `.env.local`.

### Pointing at a local backend

Run the FastAPI backend from the repo root (see the root `README.md`), then
set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` (or whatever port it
listens on).

## Commands

```bash
npm run dev         # dev server
npm run build        # production build
npm run start        # serve the production build
npm run lint          # eslint
npm run typecheck    # tsc --noEmit
npm run test           # vitest (unit/component)
npm run test:watch    # vitest watch mode
npm run test:e2e        # playwright smoke test (mocked Firebase + mocked API)
```

## Product flow

| Step | Where |
|---|---|
| Pick topic + difficulty, generate | `/dashboard` (`ExerciseForm`) |
| Preferred: navigate to the persisted exercise | `/exercises/{id}` |
| Transitional (see below): statement shown inline, no editor | `/dashboard` |
| Read statement + sample tests, write C++, submit | `/exercises/{id}` (`CppEditor` + "Verifică soluția") |
| See score / status / feedback | `/exercises/{id}` (`SubmissionResult`), only after a submission exists |
| Reveal official solution + explanation | same page, explicit "Vezi soluția oficială" click, only offered post-submission |
| Browse past exercises | `/exercises` |

`/exercises/[id]` is now the primary working page — it's where a student
actually solves an exercise, not just a read-only detail view.

## Architecture notes

- **API layer** (`lib/api.ts`): single fetch wrapper for all six
  endpoints (three live, three future — see below). Attaches
  `Authorization: Bearer <Firebase ID token>`, retries a 401 exactly once
  with a forced token refresh, normalizes every error shape into one
  `ApiError`. Mock mode is isolated entirely inside this file and
  `lib/mock-api.ts` — no component or hook branches on it.
- **Auth** (`providers/AuthProvider.tsx`, `hooks/useAuth.ts`): Firebase
  `onAuthStateChanged` is the only source of auth state. No manual token
  storage or refresh logic. `components/auth/ProtectedRoute.tsx` is **UX
  gating only**; the backend verifying the ID token and enforcing
  per-user/per-submission ownership is the real security boundary.
- **Server state**: TanStack Query exclusively. Both the generate mutation
  and the submit-solution mutation set `retry: false` explicitly (real
  AI/compute cost, and a submission is a graded record — neither should
  silently duplicate on transient failure) and disable their trigger
  button while pending.
- **Schemas — the compatibility boundary** (`schemas/exercise.ts`,
  `schemas/submission.ts`): `ExerciseSafeSchema` is the *only* shape any
  component ever sees for an exercise — `id, topic, difficulty, statement,
  created_at, sample_test_cases?`. Critically, it does **not** declare
  `solution`/`explanation`/`test_cases`, and Zod's default "strip unknown
  keys" behavior means parsing today's *actual* backend response (which
  still includes all three) through this schema silently discards them.
  This is the one place backend-compatibility logic lives — no component
  or hook needs to know the backend hasn't caught up to the target
  contract yet. `GeneratedExerciseSchema` is the equivalent tolerant union
  for `POST /exercises/generate`'s still-no-id response. See the
  **production concern** below for the residual risk this doesn't cover.
- **Editor** (`components/exercises/CppEditor.tsx`): custom, no new
  dependency — a transparent `<textarea>` (real caret/selection/keyboard
  behavior) layered over a `<pre>` rendering the same text through
  `lib/cpp-highlight.ts`, plus a scroll-synced line-number gutter and
  Tab-inserts-spaces. Chosen over Monaco to avoid its SSR/worker wiring
  cost in Next.js for a single-language editor (explicit product decision,
  not a fallback). Code state is local `useState` on the exercise page —
  survives re-renders, is not persisted to `localStorage`/anywhere else.
- **Theming**: unchanged from v1.0 — Tailwind v4 CSS-first tokens in
  `app/globals.css`, class-based dark mode, no-flash inline script. No
  design-system changes were made for this flow.

## API integrations

Live endpoints (called today):

- `POST /exercises/generate` — dashboard, generate an exercise
- `GET /exercises/` — history list (client-side topic/difficulty filtering)
- `GET /exercises/{id}` — exercise statement + metadata (response is
  filtered down to the safe shape by the schema layer, see above)

`GET /health` is not called from any page (ops/smoke-check only).

Future endpoints (wired in `lib/api.ts`/hooks, mock-mode only until the
backend ships them — see below):

- `POST /exercises/{exercise_id}/submissions` — `useSubmitSolution`
- `GET /exercises/{exercise_id}/solution` — `useOfficialSolution`

## Future Backend Dependencies

None of these exist on the backend yet. The frontend is built against
them as agreed contracts — outside mock mode, calling them today produces
a real (not faked) error through the normal error UI, since the routes
genuinely don't exist yet.

1. **`POST /exercises/{exercise_id}/submissions`** — compiles the
   student's code, runs hidden tests, returns a `Submission` (`id,
   exercise_id, score, passed_tests, total_tests, status, feedback,
   created_at`). `status` is treated as an open string on the frontend
   (`schemas/submission.ts`), not a closed enum — unrecognized future
   values fall back to a neutral, generic visual treatment instead of
   failing to parse.
2. **`GET /exercises/{exercise_id}/solution`** — should only succeed once
   the backend's authorization rules allow it (today: after ≥1
   submission). The frontend only calls it in response to an explicit user
   click and only offers that click once it already knows (this session,
   or via `has_submitted` below) that a submission exists — but the real
   gate has to be server-side.
3. **Submission-state fields on the exercise response** —
   `has_submitted`, `latest_score`, `submission_count`, `completed` are
   already declared as optional fields on `ExerciseSafeSchema` (product
   decision: these ride on the existing exercise/detail response rather
   than requiring a separate submissions-list endpoint). Until the backend
   sends them, `has_submitted` is only known within the current page visit
   (right after a successful submit) — reloading a previously-solved
   exercise won't offer "reveal solution" again until the student
   resubmits. `latest_score`/`submission_count`/`completed` are wired as
   extension points on `ExerciseCard` (history) and render nothing today.
4. **Public/hidden test-case separation** (`sample_test_cases` on the
   exercise response) — not implemented. Nothing renders pre-submission
   until the backend adds it; the frontend never assumes the current
   `test_cases` array is safe to show (see production concern below).
5. **CORS allow-list** — still not configured on the backend. Once the
   frontend's deployed origin is known it must be added, or cross-origin
   requests will fail.
6. **`X-Request-ID` response header** — `lib/api.ts` opportunistically
   reads it and `<ErrorState>` displays it when present; not sent today.
7. **Server-side history filtering/pagination**
   (`GET /exercises/?topic=&difficulty=&page=`) — filtered client-side
   over the full list today.

Firebase ID-token verification (`get_current_user` dependency, confirmed
in `src/bac_generator/api/dependencies/auth.py`) is already live on the
backend as of this iteration — no longer a gap.

## Production concern: solution/explanation are still in the raw network response

`GET /exercises/{id}` and `GET /exercises/` today still return the full
legacy shape — `solution`, `explanation`, and the complete `test_cases`
array are present in the actual HTTP response body. The frontend's schema
layer strips them before any component can render them, but that's a
**UI-level** guarantee, not a network-level one: a student opening browser
DevTools → Network can still read the official solution directly from the
raw JSON, regardless of what's rendered. Fixing this requires a backend
change — the backend should stop including those fields on this response
once submission-gating exists (item 2 above) — and is out of scope for
this frontend work per the "do not modify the backend" instruction. Flagged
here rather than worked around insecurely (e.g. by trying to intercept or
mutate the network response, which would be both fragile and pointless
against a determined user).
