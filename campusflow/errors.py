"""Shared exception hierarchy for CampusFlow.

Every module in this package signals a problem by *raising*, never by printing
and never by calling ``input()``. That single rule is what makes the business
logic directly unit-testable: a test can call ``create_ticket`` with bad data
and assert on the exception, with no stdin (standard input) and no fake terminal involved.

Only ``main.py`` catches these and turns them into a sentence for the user.
"""


class CampusFlowError(Exception):
    """Base class for every error CampusFlow raises on purpose.

    Catching this one type in ``main.py`` is enough to keep an unexpected
    input from crashing the menu loop.
    """


class ValidationError(CampusFlowError):
    """A value supplied by the user is not acceptable as given."""


class TicketNotFoundError(CampusFlowError):
    """No ticket in the collection carries the requested id."""


class InvalidTransitionError(CampusFlowError):
    """The requested status change is not legal from the ticket's status."""


class StorageError(CampusFlowError):
    """The ticket file could not be read or written safely."""
