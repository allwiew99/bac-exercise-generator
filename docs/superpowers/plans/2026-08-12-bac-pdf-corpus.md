# Bac PDF Corpus Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic PDF-to-exercise corpus pipeline that audits all raw Bac Informatics PDFs and writes only a validated preview corpus.

**Architecture:** A focused `bac_generator.ingestion` package separates extraction, normalization, classification, semantic splitting, barem parsing, retrieval mapping, and orchestration. File-level failures are retained as audit warnings and never contaminate successful documents or the existing corpus.

**Tech Stack:** Python 3.12, `pdfplumber`, Pydantic v2, pytest, mypy strict, Ruff.

## Global Constraints

- Do not modify `RetrievalDocument`.
- Use `topic="unclassified"` when deterministic classification is not reliable.
- Always leave `difficulty=None`.
- Do not infer an exam session when it is not explicitly stated.
- Never mix grading-guide text with subject exercise chunks.
- Write only `data/rag/bac_corpus.preview.json`; never overwrite `data/rag/bac_corpus.json`.
- Do not invoke Pinecone ingestion or perform any vector upsert.
- Preserve and report parsing warnings.

---

### Task 1: Internal models, normalization, and document classification

**Files:**
- Create: `src/bac_generator/ingestion/__init__.py`
- Create: `src/bac_generator/ingestion/models.py`
- Create: `src/bac_generator/ingestion/normalizer.py`
- Create: `src/bac_generator/ingestion/document_classifier.py`
- Test: `tests/unit/ingestion/test_normalizer.py`
- Test: `tests/unit/ingestion/test_document_classifier.py`

**Interfaces:**
- Produces: `DocumentType`, `BacMetadata`, `ExtractedPdf`, `ParsedExercise`, `ParsedBaremEntry`, `ParsedBacDocument`, `PdfAuditRecord`, and `BuildResult`.
- Produces: `normalize_extracted_text(text: str) -> tuple[str, tuple[str, ...]]`.
- Produces: `classify_document(text: str, source: Path) -> BacMetadata`.

- [ ] Write normalization tests that fail without Unicode normalization,
  whitespace cleanup, known assignment-glyph repair, boilerplate removal, and
  unresolved-glyph warnings.
- [ ] Run the focused normalization tests and confirm the missing-module failure.
- [ ] Implement the internal models and minimal normalizer.
- [ ] Run normalization tests until green.
- [ ] Write classification tests using misleading filenames and literal header
  fixtures for subject, barem, model, simulation, MI, SN, C/C++, and Pascal.
- [ ] Run classification tests and confirm the missing classifier failure.
- [ ] Implement content-first classification without session inference.
- [ ] Run Task 1 tests until green.

### Task 2: PDF extraction and semantic subject/barem splitting

**Files:**
- Create: `src/bac_generator/ingestion/pdf_extractor.py`
- Create: `src/bac_generator/ingestion/exercise_parser.py`
- Create: `src/bac_generator/ingestion/barem_parser.py`
- Test: `tests/unit/ingestion/test_pdf_extractor.py`
- Test: `tests/unit/ingestion/test_exercise_parser.py`
- Test: `tests/unit/ingestion/test_barem_parser.py`

**Interfaces:**
- Consumes: internal models and normalized text from Task 1.
- Produces: `extract_pdf(path: Path) -> ExtractedPdf`.
- Produces: `parse_subject(text: str, metadata: BacMetadata, source: Path) -> ParsedBacDocument`.
- Produces: `parse_barem(text: str, metadata: BacMetadata, source: Path) -> ParsedBacDocument`.

- [ ] Write extractor tests for malformed bytes and an empty extractor result;
  failures must be structured rather than uncaught dependency exceptions.
- [ ] Run extractor tests and confirm the missing implementation failure.
- [ ] Implement layout-aware extraction and file-level errors.
- [ ] Run extractor tests until green.
- [ ] Write splitting tests for both 2016-2018 and 2019-2020 layouts, including
  section spelling variants, subpoint retention, and unexpected count failure.
- [ ] Run splitting tests and confirm the missing parser failure.
- [ ] Implement section and numbered-exercise splitting with exact expected
  counts `{I: 2, II: 5, III: 4}` and `{I: 5, II: 3, III: 3}`.
- [ ] Run subject parser tests until green.
- [ ] Write and run failing tests showing that barem entries are parsed into
  separate internal records and never subject exercises.
- [ ] Implement compact answer-key and numbered-rubric parsing.
- [ ] Run all Task 2 tests until green.

### Task 3: Conservative classification and retrieval mapping

**Files:**
- Create: `src/bac_generator/ingestion/topic_classifier.py`
- Create: `src/bac_generator/ingestion/metadata_mapper.py`
- Test: `tests/unit/ingestion/test_topic_classifier.py`
- Test: `tests/unit/ingestion/test_metadata_mapper.py`

**Interfaces:**
- Consumes: `BacMetadata` and `ParsedExercise`.
- Produces: `classify_topic(text: str) -> str`.
- Produces: `classify_exercise_type(text: str) -> str`.
- Produces: `build_document_id(metadata: BacMetadata, section: str, exercise_number: int) -> str`.
- Produces: `map_retrieval_document(metadata: BacMetadata, exercise: ParsedExercise, source: Path) -> RetrievalDocument`.

- [ ] Write failing literal tests for strong topic signals, conflicting signals,
  and absent signals resulting in `unclassified`.
- [ ] Implement conservative topic and exercise-type classifiers.
- [ ] Run classifier tests until green.
- [ ] Write failing ID tests for ordinary variants, model, simulation, MI/SN,
  C/C++, and Pascal.
- [ ] Write failing mapping tests for Romanian language, section mapping,
  contextualized text, topic sentinel, and `difficulty is None`.
- [ ] Implement deterministic IDs and schema-compatible mapping.
- [ ] Run all Task 3 tests until green.

### Task 4: Corpus builder and preview-only CLI

**Files:**
- Create: `src/bac_generator/ingestion/corpus_builder.py`
- Create: `scripts/build_rag_corpus.py`
- Modify: `pyproject.toml`
- Test: `tests/unit/ingestion/test_corpus_builder.py`
- Test: `tests/unit/ingestion/test_build_rag_corpus_script.py`

**Interfaces:**
- Consumes: all parser components and `RetrievalDocument`.
- Produces: `build_corpus(raw_dir: Path) -> BuildResult`.
- Produces: `write_preview(result: BuildResult, output_path: Path) -> None`.
- The CLI defaults to `data/rag/raw/` and
  `data/rag/bac_corpus.preview.json` and prints the complete summary.

- [ ] Write failing orchestration tests with injected extraction results for
  successful subjects, separate bareme, skipped malformed files, duplicate IDs,
  warnings, schema validation, and atomic preview output.
- [ ] Run builder tests and confirm the missing implementation failure.
- [ ] Implement per-file isolation, pairing, validation, duplicate detection,
  and preview serialization.
- [ ] Run builder tests until green.
- [ ] Write a failing CLI test that verifies the existing corpus is untouched
  and no Pinecone dependency is imported or called.
- [ ] Implement the thin CLI and add the bounded `pdfplumber` dependency.
- [ ] Run all ingestion tests until green.

### Task 5: Real corpus preview and quality gates

**Files:**
- Create: `data/rag/bac_corpus.preview.json`

**Interfaces:**
- Consumes: the 68 real PDFs.
- Produces: a Pydantic-validated preview and console audit only.

- [ ] Run `scripts/build_rag_corpus.py` against the real source directory.
- [ ] Inspect counts, skipped PDFs, duplicate IDs, unresolved glyph warnings,
  subject/barem pairing, and representative chunks.
- [ ] Validate the generated JSON independently with
  `TypeAdapter(list[RetrievalDocument])`.
- [ ] Run `py_compile` over every new Python source, test, and script file.
- [ ] Run strict `mypy` over all new production Python files and the script.
- [ ] Run the relevant ingestion pytest suite and the full existing suite.
- [ ] Run Ruff over every modified/new Python file.
- [ ] Review `git diff` and confirm `data/rag/bac_corpus.json`, deployment files,
  and Pinecone ingestion code were not changed.

