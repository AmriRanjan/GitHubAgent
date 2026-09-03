# src/note.py

from langchain_core.tools import tool

@tool
def note_tool(note):

    """
    Save a note to the local notes.txt file.

    Use this tool whenever the user explicitly asks you to:
    - make a note
    - save something as a note
    - write something down
    - record information for later
    - and any other similar requests.

    The note should contain the useful information or summary that
    the user asked to save (the user's request).

    If the user asks you to investigate or explain something and also
    asks you to make a note of it, first gather the relevant information
    using the appropriate tool, then use this tool to save the findings.

    Tell the user you used this tool to save the note, and that they can view it in notes.txt.

    Args:
        note: The text or summary to save to notes.txt.
    """

    file = open("notes.txt", "a")
    file.write(note + "\n")
    file.close()