# Design decisions

Agreed by both engineers before implementation began, as required by Phase 2 of
the sprint brief. Each entry answers a question the brief asks the pair to
settle, and records *why* rather than just *what*, so a reviewer can challenge
the reasoning instead of guessing at it.

## 1. Where is the ticket collection stored, and how is it passed between the functions?

**Decision:** a plain `list` of ticket dictionaries, passed explicitly as the
first argument to every function. No global state, no class wrapper.

```python
ticket_list = []                                   # owned by main.py
ticket = create_ticket(ticket_list, ...)           # functions receive it
```

**Why:**

* It matches the brief's own example, which shows a ticket as a dictionary.
* The work queue's tie-break rule is "the earlier numeric ticket ID", and a
  list makes that ordering explicit rather than implied by dictionary insertion
  order.
* Tests can build a throwaway list inline: `ticket_list = []; create_ticket(...)`.
  No fixture loading, no setUp, no resetting shared state between tests.

**Trade-off considered:** a `dict` keyed by ticket ID would give O(1) lookup and
make duplicate IDs structurally impossible. We rejected it because it would
force the queue to sort over `.values()` and would obscure the very ordering the
brief asks us to demonstrate, while saving a linear scan over a list that will
never hold enough tickets for the difference to matter.

## 2. How does a function signal invalid input, and how does the CLI display it?

**Decision:** functions **raise**; they never print and never read input. The
CLI catches and displays.

Hierarchy in `campusflow/errors.py`:

```
CampusFlowError
├── ValidationError          the value the user supplied is unacceptable
├── TicketNotFoundError      no ticket carries that id
├── InvalidTransitionError   that status change is not legal from here
└── StorageError             the ticket file could not be read or written
```

`main.py` catches `CampusFlowError` and prints `Error: <message>`.

**Why:**

* The brief explicitly asks how we can test business logic without interactive
  input inside every test. This is the answer: because the logic layer never
  calls `input()`, a test calls `create_ticket(..., 0)` and asserts on the
  exception. No stdin, no mocking, no fake terminal.
* A single base class means the menu loop cannot be crashed by a case we forgot
  to think about — anything raised on purpose is caught in one place.
* Distinct subclasses let the CLI be more specific later (for example offering
  "reopen it first?" on `InvalidTransitionError`) without changing the logic
  layer.

## 3. What is the expected return value when a ticket is created, assigned, or updated?

**Decision:** `create_ticket`, `assign_ticket` and `change_status` each return
the ticket dictionary they operated on. Mutating functions return the same
object they mutated, so a caller can immediately read `ticket["priority"]`.

**Why:** it keeps the CLI short — `print(ticket["id"], ticket["priority"])`
instead of a second lookup — and gives tests something direct to assert on.

`get_work_queue` returns a **new sorted list**; it does not reorder the caller's
collection. Reordering in place would make the CLI's queue view destroy the
creation order that `2. List all tickets` displays.

## 4. Which module owns loading and saving JSON?

**Decision:** `campusflow/storage.py`, and it is the only module in the project
that imports `json` or touches the filesystem. `main.py` calls
`load_tickets()` and `save_tickets()`; no other module does.

**Why:** it makes the storage format a local decision. Changing to SQLite or
CSV later is a rewrite of one file with the same two function signatures.
It also makes `tests/test_storage.py` meaningful — the tests exercise the real
boundary rather than a mock of it.

**Safety behaviours chosen here:**

* Missing file → `[]`. A first run is normal, not an error.
* Malformed JSON → `StorageError`, and the file is **left exactly as it is**.
  Falling back to `[]` would mean the next save silently replaced the user's
  real tickets with an empty list. `main.py` refuses to start rather than
  promote a corrupt file into data loss.
* Saving writes to a temporary file in the same directory and `os.replace`s it
  into position, so an interrupted save cannot leave half a JSON document.

## 5. How can we test business logic without interactive input?

**Decision:** the logic layer (`tickets`, `workflow`, `reports`, `storage`)
contains no `input()` and no `print()`. All interaction is confined to
`main.py`, which contains no business rules.

**Why:** this is the single structural decision that makes the rest testable.
The test suite runs the real rule implementations directly, so a passing test
means the shipped logic is correct — not that a mock agreed with itself.

Verification: `python3 -m unittest discover -s tests -v` runs 56 tests with no
stdin and no filesystem outside a temporary directory.

---

## Judgement calls needing partner sign-off

The brief is genuinely ambiguous in three places. We chose a defensible reading
for each and have written down the alternative rather than leaving it implicit.
**Both engineers should confirm these before the first PR is merged.**

### A. What "open, unresolved tickets" means for the work queue

`campusflow/workflow.py`, `get_work_queue`.

* **Chosen:** `status == "open"` only. A ticket already `in_progress` has left
  the queue.
* **Why:** the brief names its own acceptance test *"Open-ticket queue sorted by
  priority and then numeric ID"*, and reads the phrase as a status filter.
* **Alternative:** `status != "resolved"`, i.e. show everything still needing
  attention. This is arguably more useful operationally.
* **Cost of changing:** one line, plus updating
  `test_started_and_resolved_tickets_leave_the_queue`.

### B. Exactly which status transitions are legal

`campusflow/workflow.py`, `ALLOWED_TRANSITIONS`.

* **Chosen:** exactly three moves — `open → in_progress` (only if assigned),
  `in_progress → resolved`, and `resolved → open` (reopen). Everything else,
  including `open → resolved` and `resolved → in_progress`, is rejected.
* **Why:** the brief defines the flow as `open → in_progress → resolved` and
  says a resolved ticket may only be modified after an explicit reopen. Rather
  than invent transitions the brief does not mention, we implement precisely the
  ones it does and let anything else be an error.
* **Consequence worth noting:** "a resolved ticket may only be modified after an
  explicit reopen" is read as covering `assign_ticket` too, so reassigning a
  resolved ticket raises `InvalidTransitionError`. This is the stricter reading.
* **Not decided by the brief:** whether `in_progress → open` should be allowed
  as an "abandon" move. We reject it, on the grounds that the brief never
  describes going backwards except via an explicit reopen.

### C. What counts as a valid `affected_users`

`campusflow/tickets.py`, `validate_affected_users`.

* **Accepted:** a positive `int`, or a string of digits (the CLI always supplies
  strings, so requiring callers to convert first would spread the same check
  around).
* **Rejected:** `bool`, every `float` including `12.0`, `0`, negatives, and
  non-numeric text.
* **Why the `bool` guard exists:** `isinstance(True, int)` is `True` in Python,
  so without an explicit check `True` would silently be accepted as 1 user.
  There is a test pinning this.
* **Open question:** whether `12.0` should be accepted as 12. We reject it
  rather than truncate, because the brief lists "a decimal" among the values to
  reject and a silent truncation is harder to notice than an error.

---

## Ownership

| Area | Owner |
|---|---|
| `campusflow/tickets.py`, `tests/test_tickets.py` | Engineer A |
| `campusflow/workflow.py`, `campusflow/reports.py`, `tests/test_workflow.py` | Engineer B |
| `campusflow/storage.py`, `main.py`, `tests/test_storage.py`, docs | Both |
| `campusflow/errors.py` | Both — added to the brief's suggested layout because all four modules need the shared exception types |
