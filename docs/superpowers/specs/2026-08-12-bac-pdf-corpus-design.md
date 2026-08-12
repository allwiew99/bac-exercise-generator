# Bac PDF Corpus Pipeline Design

## Goal

Build a deterministic, reviewable parser for the Romanian Bacalaureat
Informatics PDFs under `data/rag/raw/` and produce only
`data/rag/bac_corpus.preview.json`. The existing corpus and Pinecone index must
remain untouched.

## Source audit

The source directory contains 68 digitally generated PDFs from 2016 through
2020: 34 subjects and 34 corresponding grading guides. All documents expose
extractable text and explicit year, document type, profile, programming
language, and variant/model/simulation markers. Sixty PDFs do not state an exam
session; the parser must retain that uncertainty rather than translating a
variant number into a June or August session.

Every PDF contains Subiectul I, II, and III. Subject exercise boundaries are
deterministic, but extracted pseudocode contains embedded-font artifacts for
assignment arrows and some mathematical symbols. These known encodings must be
normalized, and any unresolved glyph marker must make the affected PDF
unreliable instead of entering the preview.

## Architecture

The `bac_generator.ingestion` package contains small, focused components:

- `models.py` defines internal parsing, metadata, warning, audit, and build
  result types. These types do not change the production retrieval schema.
- `pdf_extractor.py` extracts layout-aware page text with `pdfplumber` and
  reports malformed, empty, or image-only PDFs.
- `normalizer.py` normalizes Unicode and whitespace, removes page boilerplate,
  and repairs only known deterministic font artifacts.
- `document_classifier.py` classifies content using header text. Filenames may
  be reported but never override contradictory content.
- `exercise_parser.py` splits sections and numbered exercises. Subpoints remain
  attached to their parent exercise. Expected per-section exercise counts are
  validated against the published layouts for 2016-2018 and 2019-2020.
- `barem_parser.py` parses grading guides separately and links entries to the
  matching subject coordinates where possible. Barem content is never mapped
  to `RetrievalDocument` during this phase.
- `topic_classifier.py` applies conservative keyword rules. Conflicting or
  insufficient evidence produces the approved sentinel `unclassified`.
- `metadata_mapper.py` creates stable IDs and schema-compatible
  `RetrievalDocument` values.
- `corpus_builder.py` scans PDFs, isolates per-file failures, validates output,
  detects duplicate IDs, writes the preview atomically, and returns a complete
  audit summary.
- `scripts/build_rag_corpus.py` exposes the builder and prints counts, warnings,
  and per-file audit results.

## Data flow

Each PDF is extracted and classified first. Subject PDFs pass through
normalization, section splitting, exercise splitting, classification, and
retrieval mapping. Barem PDFs pass through their own parser and are retained
only in the internal build result for pairing and audit reporting. Documents
with failed extraction, incomplete metadata, incomplete sections, unexpected
exercise counts, unresolved glyphs, or duplicate IDs are skipped and reported.

Stable subject IDs include year, explicitly known session kind or the neutral
`exam` label, variant when present, profile, programming language, section, and
exercise number. For example:

`bac-2019-exam-v01-mi-cpp-s2-ex2`

Here `exam` distinguishes an ordinary exam document from an explicit model or
simulation; it does not claim a June or August session.

The retrieval `language` remains `ro`, because the field represents the natural
language of the chunk. Programming language and profile are preserved in the
ID, source context prepended to the exercise, and internal audit metadata.

## Classification rules

Topics are assigned only by deterministic textual evidence. Supported labels
include `pseudocode`, `arrays`, `matrices`, `strings`, `subprograms`,
`recursion`, `graphs`, `trees`, `divisibility`, `number processing`,
`combinatorics/backtracking`, `files`, and `algorithms`. Multiple incompatible
matches or no strong match produce `unclassified`.

Exercise type is similarly deterministic: multiple choice, pseudocode
analysis, program implementation, subprogram implementation, or open response.
Difficulty is always `None` in this phase.

## Error handling and warnings

File-level errors fail open for the build: the PDF is skipped, a structured
warning is retained, and other PDFs continue. No partially reliable PDF enters
the preview. Expected uncertainties such as an unstated exam session are
reported as warnings but do not prevent parsing. Barem pairing is based on
year, profile, explicit session kind, and variant; an unmatched or ambiguous
pair is reported.

## Schema and future metadata

`RetrievalDocument` is not modified. Useful future fields are `session`,
`variant`, `profile`, `programming_language`, `document_type`,
`paired_document_id`, `source_page`, and `parse_warnings`. They are intentionally
kept internal until the preview has been reviewed.

## Testing and verification

Unit tests cover normalization, content-based classification, semantic
splitting, conservative topic classification, deterministic IDs, retrieval
mapping, barem separation, malformed PDF handling, duplicate IDs, and
preview-only output. Verification comprises `py_compile`, strict `mypy`, the
relevant `pytest` suite, and `ruff` over all new or modified Python files.

