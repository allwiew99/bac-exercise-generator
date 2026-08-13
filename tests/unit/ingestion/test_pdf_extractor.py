from pathlib import Path

import pytest

from bac_generator.ingestion.pdf_extractor import (
    PdfExtractionError,
    _reconstruct_script_runs,
    extract_pdf,
)
from bac_generator.ingestion.safety import AMBIGUOUS_MATH_NOTATION_MARKER

_RAW_PDF_DIR = Path(__file__).parents[3] / "data" / "rag" / "raw"


def test_malformed_pdf_is_reported_as_extraction_error(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed.pdf"
    malformed.write_bytes(b"this is not a PDF")

    with pytest.raises(PdfExtractionError, match="malformed.pdf"):
        extract_pdf(malformed)


def test_missing_pdf_is_reported_as_extraction_error(tmp_path: Path) -> None:
    missing = tmp_path / "missing.pdf"

    with pytest.raises(PdfExtractionError, match="does not exist"):
        extract_pdf(missing)


def test_real_pdf_recovers_powers_and_removes_only_footer_page_numbers() -> None:
    extracted = extract_pdf(
        _RAW_PDF_DIR / "E_d_Informatica_2020_sp_MI_C_var_02_LRO.pdf"
    )
    legacy = extract_pdf(
        _RAW_PDF_DIR / "E_d_informatica_C_sp_MI_2016_var_04_LRO.pdf"
    )

    assert "144=12^2" in extracted.text
    assert "[1,10^4]" in extracted.text
    for page_number, page in enumerate(legacy.pages, start=1):
        nonempty_lines = [line.strip() for line in page.splitlines() if line.strip()]
        assert nonempty_lines[-1] != str(page_number)
    assert "1. Algoritmul alăturat" in extracted.text
    assert "n=144" in extracted.text
    assert "81112337" in legacy.text


def test_real_pdf_deduplicates_overprinted_membership_glyph() -> None:
    extracted = extract_pdf(
        _RAW_PDF_DIR / "E_d_Informatica_2019_sp_SN_C_var_simulare_LRO.pdf"
    )

    assert "n∈[2,50]" in extracted.text
    assert "∈∈" not in extracted.text


def test_real_pdf_recovers_recurrence_subscript_runs_inline() -> None:
    extracted = extract_pdf(
        _RAW_PDF_DIR / "E_d_Informatica_2019_sp_MI_C_var_01_LRO.pdf"
    )
    legacy = extract_pdf(
        _RAW_PDF_DIR / "E_d_informatica_C_sp_MI_2016_var_04_LRO.pdf"
    )

    assert "f_1=x; f_2=y; f_3=z; f_i=f_{i-1}+f_{i-2}-f_{i-3}" in extracted.text
    assert "f_n=1-2·f_{n-1}-f_{n-2}" in legacy.text


def test_real_pdf_linearizes_side_by_side_pseudocode_before_subquestions() -> None:
    extracted = extract_pdf(
        _RAW_PDF_DIR / "E_d_informatica_C_sp_MI_2016_var_04_LRO.pdf"
    )
    page = extracted.pages[0]

    intro_position = page.index("2. Se consideră algoritmul alăturat")
    code_position = page.index("Pseudocod:")
    subquestion_position = page.index("a) Scrieţi valoarea afişată")

    assert intro_position < code_position < subquestion_position
    code = page[code_position:subquestion_position]
    expected_fragments = (
        "citeşte n",
        "k(cid:1)1",
        "m(cid:1)1",
        "cât timp n>9 execută",
        "dacă n%10=[n/10]%10 atunci",
        "k(cid:1)k+1",
        "scrie m",
    )
    positions = [code.index(fragment) for fragment in expected_fragments]
    assert positions == sorted(positions)
    assert "executării │" not in page
    assert "(cid:1)" not in page[subquestion_position:]


def test_marks_small_adjacent_glyph_with_ambiguous_baseline_as_unsafe() -> None:
    chars = [
        {
            "text": "x",
            "x0": 10.0,
            "x1": 16.0,
            "top": 100.0,
            "bottom": 110.0,
            "doctop": 100.0,
            "y0": 90.0,
            "y1": 100.0,
            "height": 10.0,
            "width": 6.0,
            "adv": 6.0,
            "size": 10.0,
        },
        {
            "text": "2",
            "x0": 16.0,
            "x1": 20.0,
            "top": 102.0,
            "bottom": 108.0,
            "doctop": 102.0,
            "y0": 92.0,
            "y1": 98.0,
            "height": 6.0,
            "width": 4.0,
            "adv": 4.0,
            "size": 6.0,
        },
    ]

    reconstructed = _reconstruct_script_runs(chars)

    assert reconstructed[1]["text"] == f"{AMBIGUOUS_MATH_NOTATION_MARKER}2"


def test_real_pdf_linearizes_modern_dot_subquestions_without_false_unsafe_marker() -> None:
    extracted = extract_pdf(
        _RAW_PDF_DIR / "E_d_Informatica_2020_sp_MI_C_var_02_LRO.pdf"
    )
    page = extracted.pages[1]

    assert "⟦unsafe:unreliable_pseudocode_layout⟧" not in page
    code_position = page.index("Pseudocod:")
    subquestion_position = page.index("a. Scrieți ce se afișează")
    assert code_position < subquestion_position
    assert "înlocuind adecvat" not in page[code_position:subquestion_position]
    linear_text = " ".join(page.split())
    assert (
        "d. Scrieți în pseudocod un algoritm echivalent cu cel dat, "
        "înlocuind adecvat structura pentru...execută"
    ) in linear_text


@pytest.mark.parametrize(
    ("filename", "page_index", "subquestion"),
    (
        (
            "E_d_Informatica_C_sp_MI_2017_var_03_LRO.pdf",
            0,
            "a) Scrieţi valoarea afişată",
        ),
        (
            "E_d_Informatica_2020_sp_SN_C_var_06_LRO.pdf",
            1,
            "a. Scrieți valorile afișate",
        ),
    ),
)
def test_real_pdf_keeps_assignment_control_glyphs_out_of_prose(
    filename: str, page_index: int, subquestion: str
) -> None:
    page = extract_pdf(_RAW_PDF_DIR / filename).pages[page_index]
    subquestion_position = page.index(subquestion)

    assert "(cid:1)" not in page[subquestion_position:]
    assert "‹" not in page[subquestion_position:]
    assert "←" not in page[subquestion_position:]
