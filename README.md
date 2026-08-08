# Bac Exercise Generator

An AI-powered backend for generating, validating, and storing Romanian Baccalaureate Informatics exercises.

The application uses Large Language Models (LLMs) to generate structured programming exercises together with complete C++ solutions, explanations, and test cases. Every generated solution is automatically compiled and executed against its generated test cases before being persisted in PostgreSQL.

The project was designed with production-oriented practices, including dependency injection, layered architecture, validation, automated testing, Docker support, and cloud deployment on Google Cloud.

---

## Features

- AI-powered exercise generation
- Structured outputs using Pydantic models
- Multiple LLM providers
  - Ollama (local development)
  - Gemini through Vertex AI (production)
- Automatic retry with repair prompts
- C++ compilation and execution
- Automatic validation using generated test cases
- Business validation before persistence
- PostgreSQL persistence
- Async SQLAlchemy
- Alembic migrations
- FastAPI REST API
- Docker & Docker Compose support
- Google Cloud Run deployment
- GitHub Actions ready

---

## Architecture

```
                    FastAPI
                       │
                       ▼
               ExerciseService
                       │
     ┌─────────────────┼──────────────────┐
     ▼                 ▼                  ▼
PromptBuilder      LLM Client       ExerciseValidator
                                         │
                                         ▼
                                 CodeValidator
                                         │
                                 Compile C++
                                         │
                                 Execute Tests
                                         │
                                 Compare Output
                       │
                       ▼
              ExerciseRepository
                       │
                       ▼
                 PostgreSQL
```

---

## Technology Stack

### Backend

- Python 3.12
- FastAPI
- SQLAlchemy (Async)
- AsyncPG
- Alembic
- Pydantic v2

### AI

- Ollama
- Google Gemini
- Vertex AI

### Database

- PostgreSQL
- Supabase

### Infrastructure

- Docker
- Docker Compose
- Google Cloud Run
- Google Secret Manager
- Artifact Registry

### Testing

- Pytest
- Ruff
- MyPy

---

## Project Structure

```
src/
│
├── api/
├── ai/
├── core/
├── db/
├── repositories/
├── schemas/
├── services/
└── tests/
```

---

## Local Development

### Clone

```bash
git clone <repository>
cd BacExerciseGenerator
```

### Install

```bash
python -m venv .venv
source .venv/bin/activate

pip install -e .
```

### Environment

Create a `.env` file.

Example:

```text
DATABASE_URL=...
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder
```

### Start database

```bash
docker compose up
```

### Run migrations

```bash
alembic upgrade head
```

### Start API

```bash
uvicorn bac_generator.main:app --reload
```

---

## API

### Health Check

```
GET /health
```

---

### Generate Exercise

```
POST /exercises/generate
```

Example request

```json
{
  "topic": "vectori",
  "difficulty": "medium"
}
```

---

### List Exercises

```
GET /exercises/
```

---

### Get Exercise

```
GET /exercises/{id}
```

---

## Validation Pipeline

Every generated exercise passes through the following pipeline before being stored:

```
Generate Exercise
        │
        ▼
Validate Response Schema
        │
        ▼
Compile C++ Solution
        │
        ▼
Execute Test Cases
        │
        ▼
Compare Expected Output
        │
        ▼
Persist in PostgreSQL
```

Only fully validated exercises are stored.

---

## Testing

Run the complete test suite

```bash
python -m pytest
```

Static analysis

```bash
ruff check src tests
```

Type checking

```bash
mypy src tests
```

---

## Cloud Deployment

Production deployment uses:

- Google Cloud Run
- Google Vertex AI
- Gemini 2.5 Flash
- Google Secret Manager
- Artifact Registry
- Supabase PostgreSQL

Deployment flow:

```
GitHub
      │
Docker Build
      │
Artifact Registry
      │
Cloud Run
      │
Vertex AI
      │
Supabase
```

---

## Future Improvements

- Authentication
- User accounts
- Exercise history
- Multiple programming languages
- Difficulty estimation
- Streaming generation
- Frontend application
- Admin dashboard

---

## License

MIT