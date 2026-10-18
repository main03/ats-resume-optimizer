"""Extract plain text from an uploaded PDF."""

import io
import logging
import re

from pypdf import PdfReader
from pypdf.errors import PdfReadError

logger = logging.getLogger(__name__)

MAX_PDF_BYTES = 5 * 1024 * 1024
MAX_PDF_PAGES = 20

# PDF text often contains typographic ligatures and symbol-font bullets.
_REPLACEMENTS = str.maketrans({
    "ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl",
    " ": " ", "​": "",
    "": "•", "": "•", "": "•", "": "•", "●": "•", "▪": "•",
})


class PdfError(Exception):
    """A problem with the uploaded file, with a message safe to show the user."""


def extract_text(data: bytes) -> tuple[str, int]:
    """Return (text, page_count). Raises PdfError with a user-facing message."""
    if len(data) > MAX_PDF_BYTES:
        raise PdfError(f"The PDF is larger than {MAX_PDF_BYTES // (1024 * 1024)} MB.")
    if not data.startswith(b"%PDF"):
        raise PdfError("This file isn't a PDF.")

    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted and not reader.decrypt(""):
            raise PdfError("This PDF is password-protected. Remove the password and try again.")
        pages = reader.pages
        if len(pages) > MAX_PDF_PAGES:
            raise PdfError(f"The PDF has more than {MAX_PDF_PAGES} pages.")
        text = "\n".join(page.extract_text() or "" for page in pages)
    except PdfError:
        raise
    except (PdfReadError, ValueError, KeyError, TypeError) as e:
        logger.info("Unreadable PDF: %s", e)
        raise PdfError("This PDF couldn't be read. It may be damaged; try exporting it again.") from e

    text = clean(text)
    if len(re.sub(r"\s", "", text)) < 20:
        raise PdfError(
            "No text found in this PDF. It's probably a scanned image, which ATS can't read "
            "either. Export your resume as a text-based PDF, or paste the text instead."
        )
    return text, len(pages)


def clean(text: str) -> str:
    text = text.translate(_REPLACEMENTS)
    text = re.sub(r"[ \t]+", " ", text)            # collapse runs of spaces
    text = re.sub(r" *\n *", "\n", text)           # trim around line breaks
    text = re.sub(r"\n{3,}", "\n\n", text)         # at most one blank line
    return text.strip()
