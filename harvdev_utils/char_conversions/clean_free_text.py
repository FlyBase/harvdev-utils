"""Module:: clean_free_text.

Synopsis:
    A module to clean curated free-text in FlyBase to remove characters that
    break TSV format: i.e., tabs, newlines (optional). It also replaces
    character strings intended for internal use only with text that is more
    appropriate for public display: e.g., remove "@" indicators, replace Greek
    SGML with transliterated Greek text strings.

Author(s):
    Gil dos Santos dossantos@morgan.harvard.edu

"""

from .sgml_to_plain_text import sgml_to_plain_text
from .sub_sup_sgml_to_plain_text import sub_sup_sgml_to_plain_text

def clean_free_text(input_string, **kwargs):
    """Clean free text for public display in a TSV file.

    Args:
        input_string (str): Input free-text that needs to be cleaned.

    Kwargs:
        replace_new_lines (bool): If False, new lines will be not be removed.
                                  The default is True (new lines to be removed).

    Returns:
        cleaned_string (str): A cleaned text string.

    """
    # First remove TSV-breaking characters.
    replace_new_lines = True
    if 'replace_new_lines' in kwargs and kwargs['replace_new_lines'] is False:
        replace_new_lines = False
    cleaned_string = input_string
    if replace_new_lines is True:
        cleaned_string = cleaned_string.replace('\n', ' ')
    cleaned_string = cleaned_string.replace('\t', ' ')
    # Second, remove/replace internal-use-only text strings.
    cleaned_string = cleaned_string.replace('@', '')
    cleaned_string = sgml_to_plain_text(cleaned_string)
    cleaned_string = sub_sup_sgml_to_plain_text(cleaned_string)    

    return cleaned_string