from fastapi.testclient import TestClient

from app import main

client = TestClient(main.app)


def make_pdf(text: str) -> bytes:
    """A minimal valid one-page PDF with the given text (Helvetica)."""
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
    ]
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for i, obj in enumerate(objects, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + obj + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF" % (len(objects) + 1, xref)
    return bytes(out)


def upload(data: bytes, name="resume.pdf"):
    return client.post("/api/extract-text", files={"file": (name, data, "application/pdf")})


def test_extracts_text_from_pdf():
    res = upload(make_pdf("Senior Python developer with FastAPI experience"))
    assert res.status_code == 200
    assert res.json() == {"text": "Senior Python developer with FastAPI experience", "pages": 1}


def test_pdf_without_text_is_rejected_with_a_clear_message():
    res = upload(make_pdf(""))
    assert res.status_code == 422
    assert "scanned image" in res.json()["detail"]


def test_non_pdf_is_rejected():
    res = upload(b"hello", name="resume.docx")
    assert res.status_code == 422
    assert res.json()["detail"] == "This file isn't a PDF."
