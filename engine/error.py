class VisibleError(Exception):
    """
    Throw VisibleError from anywhere if we encounter an error we want to display to students.
    """
    pass


class InternalError(Exception):
    """
    Throw InternalError from anywhere if we encounter an error we only want to show in logs.
    """
    pass
