import os


def extract_text_from_note(note_input):
    """
    Extract text from a raw string note or a text file (.txt, .md).
    Returns a dict with 'text' and 'filename'.
    """
    if os.path.isfile(note_input):
        with open(note_input, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        filename = os.path.basename(note_input)
    else:
        content = note_input.strip()
        filename = "user_note.txt"

    return {
        "text": content,
        "filename": filename
    }
