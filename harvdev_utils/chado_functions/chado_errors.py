"""Specific chado error codes.

:synopsis: ChadoObject errors.

:moduleauthor: Christopher Tabone <ctabone@morgan.harvard.edu>, Ian Longden <ilongden@morgan.harvard.edu>
"""


class CodingError(Exception):
    """Exception raised for errors that should not happen really.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """

    def __init__(self, message):
        """Initialise error."""
        self.error = message


class DataError(Exception):
    """Exception raised for errors due to data problems.

       Example: fetching one_or_none and getting many results.
    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """

    def __init__(self, message):
        """Initialise error."""
        self.error = message
