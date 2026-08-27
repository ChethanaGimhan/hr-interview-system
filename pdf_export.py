# Turns a saved questionnaire into a PDF the interviewer can print and take
# into the room with them.

from fpdf import FPDF
from fpdf.enums import XPos, YPos

# The fonts built into fpdf2 only cover latin-1, and the model happily writes
# curly quotes and long dashes. Swap the common ones for plain ASCII so the
# text still reads properly, and anything left over is replaced rather than
# allowed to fail the whole download.
REPLACEMENTS = {
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
    "–": "-",
    "—": "-",
    "…": "...",
    " ": " ",
}


def clean(text):
    for original, plain in REPLACEMENTS.items():
        text = text.replace(original, plain)
    return text.encode("latin-1", "replace").decode("latin-1")


def safe_filename(name):
    # The candidate name comes out of a CV, so it can contain anything at all.
    # This string ends up in a response header, where a quote or a newline
    # would let the caller add headers of their own, so everything that is not
    # a plain letter or number becomes an underscore.
    cleaned = "".join(c if (c.isascii() and c.isalnum()) else "_" for c in name)
    return cleaned.strip("_") or "questionnaire"


def _line(pdf, height, text):
    # multi_cell leaves the cursor at the right hand end of whatever it just
    # wrote, so every call has to say to carry on at the left margin of the
    # next line. Leaving that out means the following call has no width left
    # to write into, and fpdf2 gives up with "not enough horizontal space".
    pdf.multi_cell(0, height, clean(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _bullets(pdf, heading, points):
    pdf.set_font("Helvetica", "B", 9)
    _line(pdf, 5, heading)
    pdf.set_font("Helvetica", "", 9)
    for point in points:
        _line(pdf, 5, f"  - {point}")
    pdf.ln(2)


def build_questionnaire_pdf(interview):
    pdf = FPDF()
    # Start a new page automatically when the current one runs out, so a long
    # questionnaire does not have to be split by hand.
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    _line(pdf, 9, interview.candidate_name)

    pdf.set_font("Helvetica", "", 10)
    _line(pdf, 6, f"{interview.job_role} - {interview.experience_years} years of experience")
    _line(pdf, 6, "Skills: " + ", ".join(interview.skills))
    pdf.ln(3)

    for number, question in enumerate(interview.questions, start=1):
        pdf.set_font("Helvetica", "B", 11)
        _line(pdf, 6, f"{number}. {question.question_text}")

        pdf.set_font("Helvetica", "I", 9)
        _line(pdf, 5, f"[{question.category}] {question.reason}")
        pdf.ln(1)

        rubric = question.rubric
        _bullets(pdf, "A strong answer covers:", rubric["strong_answer_covers"])
        _bullets(pdf, "Signs of a weak answer:", rubric["weak_answer_signs"])

        pdf.set_font("Helvetica", "B", 9)
        _line(pdf, 5, f"Follow up: {rubric['follow_up_probe']}")
        pdf.ln(5)

    # output() hands back a bytearray, and the response wants plain bytes.
    return bytes(pdf.output())
