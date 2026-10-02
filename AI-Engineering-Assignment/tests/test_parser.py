import os
import sys
import pytest

# Allow imports from the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.parser import DocumentParser

# ── helpers ──────────────────────────────────────────────────────────────────

def make_temp_pdf(tmp_path, filename="test.pdf"):
    """Create a minimal PDF using reportlab and return its path."""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    path = str(tmp_path / filename)
    doc = SimpleDocTemplate(path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("1.0 Introduction", styles["Heading2"]),
        Paragraph("This is the introduction body text.", styles["BodyText"]),
        Paragraph("2.0 Safety Instructions", styles["Heading2"]),
        Paragraph("Please follow all safety guidelines.", styles["BodyText"]),
        Paragraph("2.1 Battery Safety", styles["Heading3"]),
        Paragraph("Use only authorized batteries.", styles["BodyText"]),
        Paragraph("3.0 Error Codes", styles["Heading2"]),
        Paragraph("E1 – Pulse sensor failed.", styles["BodyText"]),
    ]
    doc.build(story)
    return path

# ── tests ─────────────────────────────────────────────────────────────────────

def test_parser_returns_nonempty_nodes(tmp_path):
    """Parser should return at least one node for a non-empty PDF."""
    pdf = make_temp_pdf(tmp_path)
    p = DocumentParser(pdf)
    nodes = p.parse(document_id=1)
    assert len(nodes) > 0, "Expected at least one node from the parsed PDF"


def test_parser_nodes_have_required_keys(tmp_path):
    """Every node dict must contain heading, content, level, content_hash."""
    pdf = make_temp_pdf(tmp_path)
    p = DocumentParser(pdf)
    nodes = p.parse(document_id=1)
    required_keys = {"heading", "content", "level", "content_hash"}
    for node in nodes:
        assert required_keys.issubset(node.keys()), (
            f"Node missing keys: {required_keys - node.keys()}"
        )


def test_parser_content_hash_is_sha256(tmp_path):
    """content_hash must be a 64-character hex string (SHA-256)."""
    pdf = make_temp_pdf(tmp_path)
    p = DocumentParser(pdf)
    nodes = p.parse(document_id=1)
    for node in nodes:
        h = node["content_hash"]
        assert isinstance(h, str) and len(h) == 64, (
            f"Expected 64-char SHA-256 hash, got: {h!r}"
        )


def test_parser_level_values_are_valid(tmp_path):
    """Level should be 0 (title), 1 (section), or 2 (subsection)."""
    pdf = make_temp_pdf(tmp_path)
    p = DocumentParser(pdf)
    nodes = p.parse(document_id=1)
    for node in nodes:
        assert node["level"] in (0, 1, 2), (
            f"Unexpected level value: {node['level']}"
        )


def test_compute_hash_is_deterministic():
    """Same heading + content must always produce the same hash."""
    p = DocumentParser.__new__(DocumentParser)
    h1 = p.compute_hash("1.0 Introduction", "Some body text.")
    h2 = p.compute_hash("1.0 Introduction", "Some body text.")
    assert h1 == h2


def test_compute_hash_differs_for_different_content():
    """Different content must produce different hashes."""
    p = DocumentParser.__new__(DocumentParser)
    h1 = p.compute_hash("1.0 Introduction", "Old content.")
    h2 = p.compute_hash("1.0 Introduction", "New content after edit.")
    assert h1 != h2
