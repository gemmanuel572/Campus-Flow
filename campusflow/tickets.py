"""Ticket creation, input validation, and the priority engine.

Owner: Engineer A (feature F1).

Everything here is a plain function over a ``list`` of ticket dictionaries that
is passed in explicitly. There is no global ticket store and no file access, so
each function can be tested in isolation with a throwaway list.

The priority engine is ordinary Python business logic - and deliberately *not* an
AI model. AI was used to learn and to review this code, not to compute
priorities at runtime.
"""

import re

from .errors import ValidationError

#: Categories the brief permits, in canonical spelling.
CATEGORIES = ("Network", "Hardware", "Software", "Other")

#: Urgency levels the brief permits.
URGENCIES = ("low", "medium", "high")

#: Priority levels this engine can return, most urgent last in the tuple below.
PRIORITIES = ("low", "medium", "high", "critical")

#: Ticket statuses in the order a ticket normally moves through them.
STATUSES = ("open", "in_progress", "resolved")

#: Sort rank used by the work queue: critical first, low last.
PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

_ID_PATTERN = re.compile(r"^T(\d+)$")
_DIGITS = re.compile(r"^[0-9]+$")


def normalize_category(value):
    """Return the canonical category for ``value``.

    Surrounding whitespace and letter case are ignored, so ``"network"``,
    ``" Network "`` and ``"NETWORK"`` all normalise to ``"Network"``.
    Raises ``ValidationError`` for anything else.
    """
    if not isinstance(value, str):
        raise ValidationError("Category must be text.")
    cleaned = value.strip().lower()
    for category in CATEGORIES:
        if category.lower() == cleaned:
            return category
    raise ValidationError(
        "Category must be one of: " + ", ".join(CATEGORIES) + "."
    )


def normalize_urgency(value):
    """Return ``value`` lower-cased and trimmed, or raise ``ValidationError``."""
    if not isinstance(value, str):
        raise ValidationError("Urgency must be text.")
    cleaned = value.strip().lower()
    if cleaned in URGENCIES:
        return cleaned
    raise ValidationError("Urgency must be one of: " + ", ".join(URGENCIES) + ".")


def validate_title(value):
    """Return the title trimmed, rejecting blank or non-text input."""
    if not isinstance(value, str):
        raise ValidationError("Title must be text.")
    cleaned = value.strip()
    if not cleaned:
        raise ValidationError("Title must not be blank.")
    return cleaned


def validate_affected_users(value):
    """Return ``affected_users`` as a positive ``int``.

    Accepts an ``int`` or a string of digits, because the CLI always hands us
    strings and making callers convert first would just spread the same check
    around. Two traps are handled explicitly:

    * ``bool`` is rejected up front - ``isinstance(True, int)`` is ``True`` in
      Python, so without that guard ``True`` would silently become 1 user.
    * floats are rejected outright rather than truncated, so ``2.5`` is an
      error instead of quietly meaning 2.
    """
    if isinstance(value, bool):
        raise ValidationError("Affected users must be a whole number.")
    if isinstance(value, int):
        number = value
    elif isinstance(value, str) and _DIGITS.match(value.strip()):
        number = int(value.strip())
    else:
        raise ValidationError(
            "Affected users must be a whole number with no decimal point."
        )
    if number <= 0:
        raise ValidationError("Affected users must be greater than zero.")
    return number


def calculate_priority(urgency, affected_users):
    """Apply the four priority rules in order and return the first match.

    Rule 1  high urgency AND 10 or more users -> critical
    Rule 2  high urgency OR  10 or more users -> high
    Rule 3  medium urgency OR 3 or more users -> medium
    Rule 4  everything else valid             -> low

    The order matters: ``high`` urgency with 12 users satisfies rules 1, 2 and
    3, and must be reported as ``critical``. Reordering these branches would
    silently break the brief's acceptance examples.
    """
    urgency = normalize_urgency(urgency)
    affected = validate_affected_users(affected_users)

    if urgency == "high" and affected >= 10:
        return "critical"
    if urgency == "high" or affected >= 10:
        return "high"
    if urgency == "medium" or affected >= 3:
        return "medium"
    return "low"


def id_number(ticket_id):
    """Return the numeric part of a ``T001``-style id, or ``None``.

    Kept public because the work queue needs the same number to break priority
    ties by "earlier numeric ticket ID".
    """
    match = _ID_PATTERN.match(str(ticket_id))
    return int(match.group(1)) if match else None


def next_ticket_id(tickets):
    """Return the next unused id in the ``T001``, ``T002``, ... series.

    The next number is derived from the tickets already in the collection
    rather than from a counter kept in memory. That is what keeps ids unique
    after a JSON reload: a saved ``T007`` pushes the next id to ``T008`` even
    though this process never created anything. Ids that do not match the
    ``T<digits>`` shape are ignored instead of crashing the app.
    """
    highest = 0
    for ticket in tickets:
        number = id_number(ticket.get("id"))
        if number is not None:
            highest = max(highest, number)
    return "T{:03d}".format(highest + 1)


def create_ticket(tickets, title, category, urgency, affected_users):
    """Validate the inputs, append a new ticket, and return it.

    Every field is validated *before* anything is appended, so a rejected
    ticket leaves no half-written record behind. The new ticket always starts
    ``open`` and unassigned; priority is computed, never supplied by the user.
    """
    clean_title = validate_title(title)
    clean_category = normalize_category(category)
    clean_urgency = normalize_urgency(urgency)
    clean_users = validate_affected_users(affected_users)

    ticket = {
        "id": next_ticket_id(tickets),
        "title": clean_title,
        "category": clean_category,
        "urgency": clean_urgency,
        "affected_users": clean_users,
        "priority": calculate_priority(clean_urgency, clean_users),
        "status": "open",
        "assigned_to": None,
    }
    tickets.append(ticket)
    return ticket
