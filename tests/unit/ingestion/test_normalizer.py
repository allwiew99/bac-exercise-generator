from bac_generator.ingestion.normalizer import normalize_extracted_text


def test_normalizes_known_pdf_artifacts_without_losing_diacritics() -> None:
    raw = (
        "  Cerință\u00a0cu   spații\r\n"
        "x(cid:1)(cid:1)(cid:1)(cid:1)1\n"
        "Pagina 1 din 3\n"
        "Probă scrisă la informatică   Varianta 4\n"
    )

    text, warnings = normalize_extracted_text(raw)

    assert text == "Cerință cu spații\nx ← 1"
    assert warnings == ()


def test_reports_unresolved_embedded_font_glyphs() -> None:
    text, warnings = normalize_extracted_text("valoare (cid:99)")

    assert text == "valoare (cid:99)"
    assert warnings == ("unresolved embedded-font glyph: (cid:99)",)


def test_normalizes_confirmed_multiplication_font_glyph() -> None:
    text, warnings = normalize_extracted_text("1(cid:215)(cid:215)(cid:215)(cid:215)3")

    assert text == "1 × 3"
    assert warnings == ()


def test_removes_repeated_pdf_header_lines() -> None:
    raw = "\n".join(
        (
            "Ministerul Educației Naționale",
            "Centrul Național de Evaluare și Examinare",
            "SUBIECTUL I (30 de puncte)",
            "1. Păstrează acest exercițiu.",
        )
    )

    text, _ = normalize_extracted_text(raw)

    assert text == "SUBIECTUL I (30 de puncte)\n1. Păstrează acest exercițiu."


def test_removes_language_footer_and_its_page_number() -> None:
    raw = "Exercițiu.\nLimbajul C/C++\n2\n"

    text, _ = normalize_extracted_text(raw)

    assert text == "Exercițiu."


def test_removes_layout_marker_before_alternate_assignment_glyph() -> None:
    text, warnings = normalize_extracted_text("││ ‹ c‹‹‹ c+1")

    assert text == "││ c ← c+1"
    assert warnings == ()


def test_removes_layout_marker_after_coordinate_deduplication() -> None:
    text, warnings = normalize_extracted_text("‹ s‹ 0\n┌pentru ‹ x‹ a,b execută")

    assert text == "s ← 0\n┌pentru x ← a,b execută"
    assert warnings == ()


def test_does_not_guess_superscripts_from_flattened_numbers() -> None:
    text, warnings = normalize_extracted_text(
        "n∈[1,109], valori din [0,104], iar exemplul este 27102"
    )

    assert text == "n∈[1,109], valori din [0,104], iar exemplul este 27102"
    assert warnings == ()


def test_collapses_only_repeated_known_membership_glyph_artifact() -> None:
    text, warnings = normalize_extracted_text(
        "n∈∈∈∈[2,50], f=2 × × x-1, iar expresiile a==b && c||d rămân neschimbate"
    )

    assert text == (
        "n∈[2,50], f=2 × x-1, iar expresiile a==b && c||d rămân neschimbate"
    )
    assert warnings == ()
