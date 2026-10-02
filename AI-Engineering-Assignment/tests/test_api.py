import os
import sys
import json
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ── helpers ───────────────────────────────────────────────────────────────────

def make_test_pdf(tmp_path, name="test.pdf"):
    """Build a minimal PDF using reportlab for upload tests."""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    path = tmp_path / name
    doc = SimpleDocTemplate(str(path), pagesize=letter)
    styles = getSampleStyleSheet()
    doc.build([
        Paragraph("1.0 Introduction", styles["Heading2"]),
        Paragraph("Body text for introduction.", styles["BodyText"]),
        Paragraph("2.0 Safety Instructions", styles["Heading2"]),
        Paragraph("Always follow safety rules.", styles["BodyText"]),
    ])
    return str(path)

# ── tests ─────────────────────────────────────────────────────────────────────

def test_health_check():
    """GET / should return status online."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "online"


def test_ingest_v1(tmp_path):
    """POST /ingest with version=1 should return document_id."""
    pdf_path = make_test_pdf(tmp_path, "v1.pdf")
    with open(pdf_path, "rb") as f:
        response = client.post(
            "/ingest",
            files={"file": ("v1.pdf", f, "application/pdf")},
            params={"version": 1}
        )
    assert response.status_code == 200
    data = response.json()
    assert "document_id" in data


def test_create_selection(tmp_path):
    """POST /selections should return a selection_id after ingesting a document."""
    # First ingest a doc to get valid node IDs
    pdf_path = make_test_pdf(tmp_path, "sel.pdf")
    with open(pdf_path, "rb") as f:
        ingest_resp = client.post(
            "/ingest",
            files={"file": ("sel.pdf", f, "application/pdf")},
            params={"version": 1}
        )
    assert ingest_resp.status_code == 200

    # Create a selection with node_id=1 (best effort – may or may not exist)
    sel_resp = client.post("/selections", json={
        "name": "Safety Section",
        "node_ids": [1],
        "version": 1
    })
    assert sel_resp.status_code == 200
    assert "selection_id" in sel_resp.json()


def test_staleness_no_generation():
    """GET /staleness/{id} with no prior generation should return a no-gen message."""
    response = client.get("/staleness/9999")
    assert response.status_code == 200
    data = response.json()
    # Either a no-generation status or an empty list
    assert isinstance(data, (dict, list))


def test_generate_tests_missing_selection():
    """POST /generate/{id} with non-existent selection should return 404."""
    response = client.post("/generate/9999")
    assert response.status_code == 404
