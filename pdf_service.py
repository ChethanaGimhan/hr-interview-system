# Pulls the plain text out of an uploaded CV, so the rest of the app can keep
# working with text the way it already does.

import io
import logging

from fastapi import HTTPException
from pypdf import PdfReader

logger = logging.getLogger(__name__)


def extract_text(pdf_bytes: bytes) -> str:
    # The file name and the content type are just text the caller typed, so
    # neither one proves anything. The first bytes of the file are the actual
    # evidence, and every real PDF starts with %PDF-.
    if not pdf_bytes.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="This file is not a PDF")
    
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = [page.extract_text() for page in reader.pages]
    except Exception as e:
        # A damaged file and a password protected one fail in different ways,
        # but the caller can do the same thing about both, so they get the same
        # message. The real reason goes to the log instead.
        logger.warning(f"Could not read the uploaded PDF: {e}")
        raise HTTPException(status_code=400, detail="This file could not be read as a PDF")

    text = "\n".join(page_text for page_text in pages if page_text)

    # A scanned CV is a photo of text, not text, so nothing comes out above.
    # Reading those needs OCR, which this project does not do.
    if len(text.strip()) < 20:
        raise HTTPException(
            status_code=400,
            detail="No text found in this PDF. If it is a scanned CV, please upload a text one",
        )

    return text
