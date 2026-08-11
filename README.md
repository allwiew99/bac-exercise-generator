# Bac Exercise Generator

A production-oriented AI application for generating, validating, solving, and evaluating Romanian Baccalaureate Informatics exercises.

The system uses Gemini 2.5 Flash through Vertex AI to generate structured programming exercises, validates the generated C++ solution inside an isolated Cloud Run sandbox, persists validated exercises in PostgreSQL/Supabase, and allows authenticated users to submit their own solutions and receive automated scores.

The project was built with a strong focus on production engineering: authentication, user isolation, distributed rate limiting, secure code execution, CI/CD, database migrations, observability, and cloud deployment.

---

## Features

- AI-powered generation of Romanian Baccalaureate Informatics exercises
- Structured LLM outputs validated with Pydantic
- Gemini 2.5 Flash through Vertex AI in production
- Ollama support for local development
- Automatic retry and repair prompts for invalid LLM responses
- Firebase Authentication
- Per-user exercise ownership and isolation
- C++ compilation and execution
- Isolated code execution through Cloud Run Sandbox
- Automatic test-case validation
- Student submission evaluation and scoring
- PostgreSQL/Supabase persistence
- Async SQLAlchemy
- Alembic migrations
- Automatic production database migrations
- Redis distributed rate limiting
- Request IDs and structured logging
- Next.js production frontend
- Docker-based backend deployment
- CI/CD through GitHub Actions
- Google Cloud Run deployment
- Google Secret Manager integration

---

## Production Architecture

```text
                    ┌──────────────────────┐
                    │   Next.js Frontend   │
                    │      Cloud Run       │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    Firebase Auth     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   FastAPI Backend    │
                    │      Cloud Run       │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        Redis Rate       Gemini 2.5       PostgreSQL /
         Limiting          Flash            Supabase
                              │
                              ▼
                       ExerciseService
                              │
                              ▼
                       ExerciseValidator
                              │
                              ▼
                      Cloud Run Sandbox
                              │
                              ▼
                        clang++ + lld
                              │
                              ▼
                       Execute Test Cases
                              │
                              ▼
                         Persist Result
Exercise Generation Flow
Authenticated User
        │
        ▼
Generate Request
        │
        ▼
Distributed Rate Limit
        │
        ▼
Gemini 2.5 Flash
        │
        ▼
Structured Response Validation
        │
        ▼
Business Validation
        │
        ▼
C++ Compilation
        │
        ▼
Sandboxed Execution
        │
        ▼
Test Case Validation
        │
        ▼
Persist Exercise
        │
        ▼
Return Safe Exercise View
Submission Flow
Authenticated User
        │
        ▼
Submit C++ Solution
        │
        ▼
Distributed Rate Limit
        │
        ▼
Verify Exercise Ownership
        │
        ▼
Compile in Sandbox
        │
        ▼
Execute Against Test Cases
        │
        ▼
Calculate Score
        │
        ▼
Persist Submission
        │
        ▼
Return Score + Feedback
Technology Stack
Backend
Python 3.12
FastAPI
Pydantic v2
SQLAlchemy Async
AsyncPG
Alembic
AI
Google Gemini 2.5 Flash
Vertex AI
Ollama for local development
Authentication
Firebase Authentication
Firebase Admin SDK
Database
PostgreSQL
Supabase
Distributed Infrastructure
Redis
Google Cloud Run
Cloud Run Sandbox
Google Secret Manager
Artifact Registry
VPC networking
Frontend
Next.js 16
React 19
TypeScript
Firebase Web SDK
TanStack Query
Zod
Tailwind CSS
Code Execution
Clang
LLD
Isolated Cloud Run Sandbox execution
Testing & Quality
Pytest
Vitest
Playwright
Ruff
MyPy
ESLint
TypeScript type checking
CI/CD
GitHub Actions
Docker
Artifact Registry
Automated Alembic production migrations
Automated Cloud Run deployment
Project Structure
.
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── tests/
│
├── src/
│   └── bac_generator/
│       ├── ai/
│       ├── api/
│       ├── core/
│       ├── db/
│       ├── models/
│       ├── repositories/
│       ├── schemas/
│       └── services/
│
├── tests/
│   ├── integration/
│   └── unit/
│
├── alembic/
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
Local Development
Backend

Create a Python environment:

python -m venv .venv
source .venv/bin/activate

Install dependencies:

pip install -e ".[dev]"

Create .env from the example:

cp .env.example .env

Run PostgreSQL:

docker compose up -d

Run migrations:

alembic upgrade head

Start the API:

uvicorn bac_generator.main:app --reload
Frontend

Install dependencies and start the development server:

cd frontend
npm install
npm run dev

The frontend requires Firebase public configuration and the backend API URL through NEXT_PUBLIC_* environment variables.

Expected variables include:

NEXT_PUBLIC_API_BASE_URL
NEXT_PUBLIC_FIREBASE_API_KEY
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN
NEXT_PUBLIC_FIREBASE_PROJECT_ID
NEXT_PUBLIC_FIREBASE_APP_ID
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID
NEXT_PUBLIC_USE_MOCK_API
API
Health Check
GET /health
Generate Exercise
POST /exercises/generate
List User Exercises
GET /exercises/
Get Exercise
GET /exercises/{exercise_id}
Submit Solution
POST /exercises/{exercise_id}/submissions

All exercise and submission endpoints require Firebase authentication.

Validation Pipeline

Every generated exercise passes through the following pipeline before persistence:

Generate Exercise
        │
        ▼
Validate Structured Response
        │
        ▼
Apply Business Rules
        │
        ▼
Compile C++ Solution
        │
        ▼
Execute Generated Test Cases
        │
        ▼
Compare Actual vs Expected Output
        │
        ▼
Persist Validated Exercise

Only exercises that pass validation are persisted.

Security

The application includes several production-oriented security controls:

Firebase ID token verification
Per-user resource ownership
CORS restricted to configured origins
Distributed Redis rate limiting
C++ execution inside an isolated sandbox
No outbound network access from submitted code execution
Database credentials stored in Google Secret Manager
Production secrets are not committed to the repository
Request IDs for traceability
HTTPS-aware proxy handling behind Cloud Run
Rate Limiting

Production uses Redis-backed distributed rate limiting.

Current limits:

Exercise generation: 10 requests / 60 seconds / user
Solution submission: 30 requests / 60 seconds / user

The distributed implementation ensures consistent limits even when Cloud Run scales to multiple backend instances.

Production testing confirmed that the submission rate limiter responds with:

429 Too Many Requests

after the configured threshold is exceeded.

Testing
Backend

Run the full backend test suite:

pytest -q

Static analysis:

ruff check .

Type checking:

mypy src

Current backend test suite:

76 tests passing
Frontend

Run frontend quality checks:

cd frontend
npm run lint
npm run typecheck
npm run test
npm run build

Current frontend test suite:

57 tests passing

The production Next.js build has also been validated successfully.

CI/CD

GitHub Actions performs:

Checkout
   ↓
Install Python dependencies
   ↓
Start PostgreSQL service
   ↓
Run Alembic migrations
   ↓
Run Ruff
   ↓
Run MyPy
   ↓
Run Pytest
   ↓
Build Docker image
   ↓
Push image to Artifact Registry
   ↓
Update Cloud Run migration job
   ↓
Run production Alembic migrations
   ↓
Deploy backend to Cloud Run

The production deployment also configures:

Gemini / Vertex AI
Firebase project
Cloud Run Sandbox
Redis rate limiting
VPC networking
production CORS
Secret Manager database credentials
Production Deployment
Backend

The backend runs on Google Cloud Run in:

europe-west1

Production uses:

LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash
CODE_RUNNER_PROVIDER=sandbox
RATE_LIMITER_PROVIDER=redis

Database credentials are injected through Google Secret Manager.

Frontend

The Next.js frontend is also deployed to Google Cloud Run.

The frontend communicates directly with the production FastAPI backend and authenticates users using Firebase Authentication.

Production Validation

The production environment has been validated end-to-end for:

health checks
authentication boundaries
HTTPS proxy handling
production CORS
frontend authentication
exercise generation
exercise persistence
C++ sandbox compilation
C++ sandbox execution
test-case validation
student submissions
automated scoring
Redis rate limiting
CI/CD deployment

A production submission has successfully returned:

100 / 100

with all generated test cases passing.

Redis production validation also confirmed:

Requests 1-30 → accepted
Request 31     → 429 Too Many Requests
Observability

The backend includes:

structured application logging
request IDs
Cloud Run logs
Cloud Trace correlation headers
LLM latency logging
validation and execution error logging

These provide traceability across production requests and make failures easier to diagnose.

Current Status
Production hardening: complete
Backend deployment: operational
Frontend deployment: operational
Firebase authentication: operational
Gemini generation: operational
Cloud Run Sandbox: operational
PostgreSQL/Supabase persistence: operational
Redis distributed rate limiting: validated
CI/CD: operational
Production smoke tests: passed
RAG / Vector Database Roadmap

RAG and vector retrieval are not currently implemented.

A future version will introduce:

Pinecone vector database
document ingestion
chunking
embeddings
semantic retrieval
metadata filtering
retrieval-augmented exercise generation
optional hybrid search
reranking
retrieval evaluation

Planned metadata includes:

topic
difficulty
bac_section
year
source
exercise_type

The planned retrieval flow is:

Baccalaureate exercises / solutions / grading material
                    │
                    ▼
              Document Ingestion
                    │
                    ▼
                  Chunking
                    │
                    ▼
                 Embeddings
                    │
                    ▼
                 Pinecone
                    │
                    ▼
          Semantic / Hybrid Search
                    │
                    ▼
             Retrieved Context
                    │
                    ▼
            Gemini 2.5 Flash
                    │
                    ▼
           Exercise Generation

Pinecone is planned as a post-production enhancement and is intentionally not listed as an implemented component of the current architecture.

Future Improvements

Potential post-v1 improvements include:

Pinecone-based RAG
hybrid retrieval and reranking
retrieval evaluation
improved exercise difficulty calibration
richer progress tracking
frontend UX improvements
analytics and monitoring dashboards
additional exercise categories
richer feedback for incorrect submissions
## License

This project is licensed under the MIT License. See the `LICENSE` file for details.