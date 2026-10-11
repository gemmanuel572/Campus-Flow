# CampusFlow

A command-line helpdesk ticket manager for Learn2Earn campus technical support.

## The problem

Campus staff report Wi-Fi outages, faulty laptops, broken development
environments and inaccessible platforms, usually informally. Requests arrive by
chat, by email, and in person, and they get lost. CampusFlow records each
request as a ticket, works out how urgent it is, lets you assign it to a staff
member, tracks it from open to resolved, and keeps everything in a JSON file so
nothing disappears when the program closes.

## Team

| Fellow | Role | Owns |
|---|---|---|
| _(Engineer A - add your name)_ | Engineer A | Ticket creation, input validation, priority engine (F1), `tests/test_tickets.py` |
| _(Engineer B - add your name)_ | Engineer B | Assignment, lifecycle, work queue, reports (F3–F6), `tests/test_workflow.py` |

Both engineers co-owned JSON persistence (F7), integration, and `main.py`.

## Requirements

* Python 3.8 or newer. Developed and tested on **Python 3.12.3**.
* No third-party packages. CampusFlow uses only the standard library
  (`json`, `unittest`, `re`, `pathlib`, `tempfile`).

## Setup

```bash
git clone https://github.com/gemmanuel572/Campus-Flow.git
cd Campus-Flow
```

There is nothing to install. Check your interpreter if you like:

```bash
python3 --version
```

## Running the CLI

Run it from the repository root, because the default data file path is relative
to the working directory:

```bash
python3 main.py
```

You will see:

```
CampusFlow - campus technical support tickets
---------------------------------------------
  1. Create a ticket
  2. List all tickets
  3. View one ticket
  4. Assign a ticket
  5. Change ticket status
  6. Show work queue
  7. Show report
  8. Save to disk
  9. Exit
```

The menu keeps running until you choose **9**. Tickets are saved to disk
automatically when you exit, and option 8 saves at any point. Menu text is
entered as typed; surrounding spaces and letter case are ignored, so `network`,
` Network ` and `NETWORK` are all accepted.

### Worked example

```
Choose an option: 1
Title: Campus Wi-Fi is down
Category (Network/Hardware/Software/Other): Network
Urgency (low/medium/high): HIGH
Affected users: 15

Created T001 with priority critical.
```

## Running the tests

```bash
python3 -m unittest discover -s tests -v
```

**What the tests cover** — 56 tests, all passing:

| File | Tests | Covers |
|---|---|---|
| `tests/test_tickets.py` | 28 | The four priority rules and their boundaries; `affected_users` rejected when zero, negative, decimal, text, or a bool; blank titles; invalid urgency and category; case normalisation; sequential and unique IDs; rejected tickets leaving no partial record |
| `tests/test_workflow.py` | 20 | Assignment and blank-name rejection; unknown ticket IDs; a resolved ticket refusing reassignment; the `open → in_progress → resolved` path; rejecting an unassigned start, a skipped step, and `resolved → in_progress`; reopening; queue ordering and numeric tie-breaks |
| `tests/test_storage.py` | 8 | Save/reload round-trip; missing file starting fresh; creating the data directory; malformed JSON raising without destroying the file; non-list JSON rejected; IDs staying unique across a reload; no temporary files left behind |

## How priority is calculated

Priority is **plain Python logic, not an AI model**. The rules are checked in
this exact order and the **first match wins**:

| Rule | Condition | Priority |
|---|---|---|
| 1 | high urgency **and** 10 or more affected users | `critical` |
| 2 | high urgency **or** 10 or more affected users | `high` |
| 3 | medium urgency **or** 3 or more affected users | `medium` |
| 4 | everything else valid | `low` |

The order matters. A high-urgency ticket with 12 users satisfies rules 1, 2 and
3 at once, and must come out as `critical`. See `campusflow/tickets.py`,
`calculate_priority`.

## How status changes work

```
open ──► in_progress ──► resolved
  ▲                          │
  └──────── reopen ──────────┘
```

* `open → in_progress` requires the ticket to be **assigned first**.
* `in_progress → resolved` finishes the work.
* `resolved → open` is the **explicit reopen**. A resolved ticket must go
  through this before it can change again — which is why it cannot be
  reassigned or moved straight back to `in_progress`.

## Where tickets are saved

Tickets live in `data/tickets.json`, relative to the directory you run the
program from. The file is created on the first save and its directory is
created if missing.

* **To start fresh**, stop the program and delete `data/tickets.json`.
* `data/` is in `.gitignore`, so your tickets and your teammate's tickets never
  end up in a commit or collide in a merge.

If `data/tickets.json` exists but is not valid JSON, CampusFlow refuses to
start and tells you the parse error rather than starting empty. That is
deliberate: starting empty would mean the next save silently overwrote your
real tickets with nothing. The file is left exactly as it is so you can repair
or remove it.

## Known limitations

* **The work queue shows `open` tickets only.** The brief says "show open,
  unresolved tickets"; we read that literally, so a ticket already
  `in_progress` has left the queue. If the team prefers "everything not yet
  resolved", it is a one-line change in `campusflow/workflow.py`
  (`get_work_queue`) — see `docs/design-decisions.md`.
* **No concurrent use.** Tickets are loaded once at startup and written at
  save. Two people running the CLI against the same file will overwrite each
  other; last save wins.
* **No search, filtering, or pagination.** `2. List all tickets` prints every
  ticket, which is fine for a campus queue but not for thousands of rows.
* **No authentication.** Anyone who can run the command can see and change
  every ticket.
* **Tickets are never deleted.** There is no close/archive flow beyond
  `resolved`, and no way to remove a ticket created by mistake.
* **`affected_users` is a snapshot.** It is the count given at creation and is
  not updated as more people report the same problem.
* **Id generation assumes the `T<digits>` shape.** Unrecognised IDs are skipped
  when computing the next number rather than raising, so a hand-edited file
  with odd IDs will not crash, but it will not be repaired either.

## Future improvements

1. Delete/archive tickets, and merge duplicates so `affected_users` can grow as
   more reports arrive — which would also change priority, so it needs a
   decision about whether to recompute on update.
2. Persist after every change instead of at exit, so a crash loses nothing.
3. An `in_progress` view or per-assignee queue, since the current queue hides
   work already underway.

## Project documents

* [`docs/design-decisions.md`](docs/design-decisions.md) — the interfaces both
  engineers agreed on before coding, and the judgement calls behind them.
* [`docs/ai-learning-log.md`](docs/ai-learning-log.md) — each engineer's
  AI-assisted learning entries, with the experiments used to verify them.
* [`EXPLANATION.txt`](EXPLANATION.txt) — a plain-text walkthrough of the whole
  codebase, for revision and the technical defence.

## Pull requests

_(Add links to both reviewed PRs before submission.)_

* Engineer A's PR: #
* Engineer B's PR: #
