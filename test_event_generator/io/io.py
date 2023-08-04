"""Methods for input puml files and output tests
"""


def load_utf_file_from_path(file_path: str) -> str:
    """Method to load a text file from a given path and read it to a variable

    :param file_path: The path to the file
    :type file_path: `str`
    :return: Returns the read in file as a string
    :rtype: `str`
    """
    with open(file_path, 'r', encoding="utf8") as file:
        read_file = file.read()
    return read_file


def load_puml_file_from_path(file_path: str) -> str:
    """Method to load puml file and raise error if file is not puml

    :param file_path: The path to the file
    :type file_path: `str`
    :raises RuntimeError: Raises error if the file is not a valid puml file
    :return: Returns the read in file as a string
    :rtype: `str`
    """
    file = load_utf_file_from_path(file_path)
    # check for start and end of puml file
    if "@startuml" not in file or "@enduml" not in file:
        raise RuntimeError("File is not a valid puml file")
    return file
