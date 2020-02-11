class CodingError(Exception):
    """Exception raised for errors that should not happen really.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """

    def __init__(self, message):
        self.error = message


class DataError(Exception):
    """Exception raised for errors due to data problems.
       Example: fetching one_or_none and getting many results.
    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """

    def __init__(self, message):
        self.error = message
