# Bac PDF Corpus Hardening Design

## Goal

Regenerate a reviewable retrieval preview from the existing 68 Bac PDFs after
removing systematic layout artifacts. The production corpus, retrieval schema,
and Pinecone index remain untouched.

## Root causes

The original extractor converted each page to plain layout text before the
normalizer ran. That discarded the evidence needed to distinguish a centered
footer number, a raised exponent, a lowered recurrence index, and two columns
sharing the same vertical position. Repeated membership symbols are duplicate
paint operations at the same coordinates. Graph diagrams are PDF vector
objects and therefore have no text representation. Shared section directions
appear between numbered item groups and are consequently captured by the
preceding exercise.

## Architecture

`pdf_extractor.py` becomes the geometry-aware boundary. It deduplicates
overprinted characters, removes only isolated centered numeric words in the
bottom footer band, reconstructs high-confidence superscript and subscript
runs from relative font size and baseline displacement, and linearizes
deterministic side-by-side pseudocode blocks. Ambiguous script or pseudocode
layout is represented by a private unsafe marker; it is never guessed.

`normalizer.py` retains a narrow fallback for repeated known mathematical
glyphs and does not collapse arbitrary characters. `exercise_parser.py`
removes only full-line, recognized section directions before splitting. After
all expected boundaries and numbering have been validated, it applies
exercise-level safety checks:

- graph/tree text requiring an adjacent visual is excluded unless a complete
  matrix, parent vector, or explicit edge/arc representation is present;
- ambiguous layout notation is excluded as `ambiguous_math_notation`;
- unreconstructable side-by-side pseudocode is excluded as
  `unreliable_pseudocode_layout`.

Safe exercises from the same PDF remain eligible. Internal ingestion models
record stable exercise coordinates, source, and reason for every exclusion.
The CLI prints those records in the build report. No new field is added to
`RetrievalDocument`.

## Confidence rules

A script run is reconstructed only when its characters are materially smaller
than an adjacent baseline character and are consistently displaced above or
below that baseline. A contiguous run receives one `^` or `_` prefix. A small
adjacent alphanumeric run without a confident direction receives an unsafe
marker.

A footer page number must be a one-to-three-digit word, be the only word on its
visual line, lie in the bottom ten percent of the page, and be centered within
ten percent of page width. Numeric exercise content outside that region is
preserved.

A side-by-side pseudocode block is linearized only when the page contains an
explicit pseudocode introduction and a stable right-column boundary supported
by control-structure glyphs. Introductory prose is emitted first, then a
`Pseudocod:` block in top-to-bottom order, then exercise subquestions. A block
without those signals is marked unsafe.

## Validation

Tests use literal text/character fixtures plus direct regression checks against
the affected repository PDFs. The build validates every retained entry as a
`RetrievalDocument`, leaves `difficulty=None`, preserves `unclassified`, and
writes only `data/rag/bac_corpus.preview.json`. Corpus-wide scans and a manual
review of at least 30 complete documents determine ingestion readiness.
