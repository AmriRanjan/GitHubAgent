from langchain_core.tools import tool

@tool
def note_tool(note):
    """
    Description: 
        Saves a note to a local file

    Arguments:
        note: this is the text note to save
    """

    file = open("notes.txt", "a")
    file.write(note + "\n")
    file.close()