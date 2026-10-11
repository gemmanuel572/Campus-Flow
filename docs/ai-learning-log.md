# AI learning log

One entry per meaningful AI interaction, minimum **three per fellow**, with at
least one per fellow documenting a suggestion you **corrected, improved or
rejected** after checking it.

> **This file is a template.** The `Prompt to AI`, `Useful AI guidance` and
> `Decision` sections are blank on purpose. The brief requires this log to be
> truthful and states that fabricating a flaw or claiming to have verified
> something you did not run does not count. Two of the five AI-native marks
> (out of 20) are specifically for the *credibility* of this log — an honest
> short entry scores better than a polished invented one.
>
> The `My independent experiment` section of each entry below is **already
> written** as a concrete, runnable experiment. Run it, paste the real output,
> and record what you concluded. Do not past results you did not see.

---

## Fellow: _(Engineer A — add your name)_

### Interaction #1 — `json.dump()` / `json.load()` round-tripping

**Problem:** I need tickets to survive a restart, and I was not confident about
the difference between writing a Python object to a file and writing text to a
file.

**My initial understanding:**
_(In your own words, before asking. Do not skip this — the log is checked
against your understanding at the time.)_

**Prompt to AI:**
_(Paste the actual prompt you sent. Ask for a small example unrelated to
CampusFlow — the brief asks for this deliberately, so you learn the concept
instead of copying project code.)_

**Useful AI guidance:**
_(Brief summary in your own words.)_

**My independent experiment** — run this and record the real output:

```bash
python3 -c "
import json
data = [{'id': 'T001', 'affected_users': 15, 'assigned_to': None}]
text = json.dumps(data)
print('as text:', text)
print('type back:', type(json.loads(text)))
print('None survived as:', json.loads(text)[0]['assigned_to'])
"
```

Before running it, write down what you predict `print(text)` shows and whether
`assigned_to` comes back as `None` or the string `"None"`.

**Verification source or result:**
_(Paste the actual terminal output. Note whether your prediction was right.)_

**Decision:** _(Accepted / improved / rejected — and why.)_

**Related file/commit:** `campusflow/storage.py`

**What I can now explain without AI:**
_(Two or three sentences, in your words, that you could say in the defence.)_

---

### Interaction #2 — Why `isinstance(True, int)` is a validation trap

**Problem:** `validate_affected_users` must reject text and decimals. I wanted
to know whether a plain `isinstance(value, int)` check was sufficient and
whether `True` would sneak through.

**My initial understanding:**
_(In your own words.)_

**Prompt to AI:**
_(Your actual prompt.)_

**Useful AI guidance:**
_(Brief summary.)_

**My independent experiment** — run this and record the real output:

```bash
python3 -c "
print('isinstance(True, int):', isinstance(True, int))
print('True as a number:', int(True))
print('True >= 1:', True >= 1)
print('bool is a subclass of int:', bool.__mro__)
"
```

Predict the four lines before you run it. The important one is the last: it
shows *why* `True` passes an `int` check — `bool` inherits from `int` in
Python, so a ticket with `affected_users=True` would quietly be recorded as
1 user and pass validation.

**Verification source or result:**
_(Paste the real output, then confirm the guard is actually load-bearing by
temporarily deleting the `isinstance(value, bool)` check in
`campusflow/tickets.py` and re-running: `python3 -m unittest discover -s tests
-v`. Which test fails? Restore the check afterwards.)_

**Decision:** _(Accepted / improved / rejected — and why.)_

**Related file/commit:** `campusflow/tickets.py`,
`tests/test_tickets.py::AffectedUsersValidationTests::test_bool_is_rejected`

**What I can now explain without AI:**
_(In your words.)_

---

### Interaction #3 — _(your choice, from debugging or reviewing your own code)_

Pick something that actually came up while you were working. The brief's own
suggested topics are JSON persistence, exception handling, `unittest`
assertions, safe list operations, Git branches, or PR review. Whatever you
choose, it needs the same shape: what you did not understand, a small
experiment, the real output, and what you concluded.

**Problem:**

**My initial understanding:**

**Prompt to AI:**

**Useful AI guidance:**

**My independent experiment:**

**Verification source or result:**

**Decision:**

**Related file/commit:**

**What I can now explain without AI:**

---

## Fellow: _(Engineer B — add your name)_

_Engineer B: repeat the same structure for your own three entries. Good
candidates from your half of the code:_

1. **Sorting with a compound key.** The work queue sorts by priority *then* by
   numeric ID. Ask AI about `sorted(..., key=...)` and tuples, then experiment
   with why sorting the IDs as text gives `T010` before `T002`:

   ```bash
   python3 -c "
   ids = ['T010', 'T002', 'T001']
   print('as text:  ', sorted(ids))
   print('as numbers:', sorted(ids, key=lambda i: int(i[1:])))
   "
   ```

   There is a test pinning this:
   `test_tie_break_uses_numeric_not_lexical_order`.

2. **Sets, or dictionaries, for allowed transitions.** Ask about modelling
   "which moves are legal from here" and compare a `dict` of tuples against a
   set of `(from, to)` pairs. Then check a transition that is *not* in
   `ALLOWED_TRANSITIONS` and confirm it raises.

3. **`unittest` assertions for "this must raise".** `assertRaises` as a context
   manager, and why asserting that a function raised is not the same as
   asserting the state was left unchanged — inspect
   `test_unassigned_ticket_cannot_start`, which checks both the exception *and*
   that the status is still `open`.

---

## Final reflection (each fellow answers, for submission)

1. Which feature did you personally implement, and how do you know it works?
2. What did AI teach you that you did not understand at the start?
3. Give one example where you verified, changed, or rejected an AI suggestion.
4. What did you learn from reviewing your partner's PR?
5. What would you improve next if the team had another hour?
