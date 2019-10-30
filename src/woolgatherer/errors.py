"""
Exceptions specifc to feedback
"""


class InvalidOperationError(RuntimeError):
    """ An operational error occurred """


class InsufficientCapacityError(RuntimeError):
    """ Do not have the capacity to complete a requested operation """
