# Bac PDF Corpus Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair geometry-dependent extraction defects, exclude unsafe exercises with reasons, and regenerate a validated preview corpus.

**Architecture:** Character geometry is repaired before plain-text normalization. Section cleanup and exercise safety decisions remain separate, deterministic parser stages, while the corpus builder records exercise-level exclusions without changing `RetrievalDocument`.

**Tech Stack:** Python 3.12, pdfplumber, Pydantic v2, pytest, mypy strict, Ruff.

## Global Constraints

- Never modify `data/rag/bac_corpus.json` or ingest/upsert into Pinecone.
- Write only `data/rag/bac_corpus.preview.json`.
- Do not change `RetrievalDocument`.
- Keep `difficulty=None` and use `topic="unclassified"` when uncertain.
- Do not infer an unstated exam session.
- Do not use OCR, image understanding, or an LLM.
- Exclude any exercise whose required notation or visual cannot be reconstructed confidently.

---

### Task 1: Geometry-aware character extraction

**Files:**
- Modify: `src/bac_generator/ingestion/pdf_extractor.py`
- Test: `tests/unit/ingestion/test_pdf_extractor.py`

**Interfaces:**
- Produces: deduplicated page text with script runs represented by `^`/`_` and footer page numbers removed.
- Preserves: `extract_pdf(path: Path) -> ExtractedPdf`.

- [ ] Add real-PDF regressions for `144=12^2`, recurrence indices, one repeated membership symbol, and footer removal while preserving exercise numbers.
- [ ] Run those tests and verify failures against the current extractor.
- [ ] Implement exact-coordinate deduplication, baseline-aware script reconstruction, and positional footer filtering.
- [ ] Run the extractor regressions until green.

### Task 2: Normalization and shared section directions

**Files:**
- Modify: `src/bac_generator/ingestion/normalizer.py`
- Modify: `src/bac_generator/ingestion/exercise_parser.py`
- Test: `tests/unit/ingestion/test_normalizer.py`
- Test: `tests/unit/ingestion/test_exercise_parser.py`

**Interfaces:**
- Produces: known-glyph normalization without arbitrary repeated-character collapse.
- Produces: numbered exercises without recognized full-line section directions.

- [ ] Add failing literal regressions for repeated `∈`, legitimate repeated operators, the known leaked direction, and exercise-specific instructions.
- [ ] Implement the narrow glyph rule and exact folded shared-direction removal.
- [ ] Run normalization and splitting tests until green.

### Task 3: Exercise-level safety and reporting

**Files:**
- Modify: `src/bac_generator/ingestion/models.py`
- Modify: `src/bac_generator/ingestion/exercise_parser.py`
- Modify: `src/bac_generator/ingestion/corpus_builder.py`
- Modify: `scripts/build_rag_corpus.py`
- Test: `tests/unit/ingestion/test_exercise_parser.py`
- Test: `tests/unit/ingestion/test_corpus_builder.py`

**Interfaces:**
- Produces: `ExcludedExercise` records with section, exercise number, and reason.
- Produces: `BuildResult.excluded_exercises` for the CLI report.

- [ ] Add failing tests excluding a visual-only graph, retaining a complete adjacency matrix, and retaining safe siblings from the same subject.
- [ ] Add failing tests for ambiguous notation and pseudocode exclusion reasons.
- [ ] Implement post-boundary safety assessment and builder aggregation.
- [ ] Run parser and builder tests until green.

### Task 4: Side-by-side pseudocode reading order

**Files:**
- Modify: `src/bac_generator/ingestion/pdf_extractor.py`
- Test: `tests/unit/ingestion/test_pdf_extractor.py`

**Interfaces:**
- Produces: prose introduction, a contiguous `Pseudocod:` block, then subquestions.
- Produces: an unsafe marker when a detected two-column block lacks a stable boundary.

- [ ] Add a failing regression against the 2016 side-by-side sample proving code no longer interrupts prose.
- [ ] Implement column-boundary detection from structure glyph geometry and deterministic block linearization.
- [ ] Run the extractor and ingestion suites until green.

### Task 5: Preview regeneration and review

**Files:**
- Modify: `data/rag/bac_corpus.preview.json`

**Interfaces:**
- Produces: validated safe retrieval documents and a printed exclusion report.

- [ ] Run `scripts/build_rag_corpus.py` and validate every JSON entry independently.
- [ ] Run corpus-wide scans for all requested defect classes and duplicate/short content.
- [ ] Review at least 30 complete documents across all required dimensions.
- [ ] Run `py_compile`, strict `mypy`, repository-wide Ruff, focused ingestion tests, and full pytest.
- [ ] Confirm the production corpus checksum is unchanged and no Pinecone command ran.
