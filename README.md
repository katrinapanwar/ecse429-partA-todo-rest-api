# ECSE 429 — Todo Manager REST API Unit Test Suite

Unit tests for Part A of the ECSE 429 course project, built from findings
documented in `ECSE429_Exploratory_Testing_Log.xlsx`.

## Setup

1. Make sure the Todo Manager REST API is running:
   ```
   java -jar runTodoManagerRestAPI-1.5.5.jar
   ```
   It should say `Running on 4567`. Leave this terminal open.

2. In a separate terminal, install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the tests

Run the whole suite:
```
pytest
```

Run a single file:
```
pytest tests/test_crud.py
```

Run with more detail on xfail/xpass results (useful to confirm the
documented-vs-actual bug pairs are behaving as expected):
```
pytest -rx
```

### Running in random order (required for the unit test video)

`pytest-randomly` is included in `requirements.txt` and is **enabled by
default** once installed — no flags needed. Every run uses a different
random seed and prints it at the top of the output, e.g.:
```
Using --randomly-seed=1234567
```
To **re-run the exact same random order** again (e.g. to compare two runs):
```
pytest -p randomly --randomly-seed=1234567
```

For the required video, run the suite at least twice and show the
`Using --randomly-seed=...` line differing between runs, demonstrating the
tests pass regardless of execution order (a direct consequence of each test
creating and cleaning up its own data via fixtures in `conftest.py`, rather
than depending on shared or hardcoded state).

## Project structure

```
todo_api_tests/
├── conftest.py                              # shared fixtures & helpers
├── pytest.ini                               # pytest config
├── requirements.txt
├── README.md
└── tests/
    ├── test_crud.py                         # Section A: core CRUD
    ├── test_validation.py                   # Section B: field validation
    ├── test_id_addressing.py                # Section C: id edge cases
    ├── test_malformed_and_content_negotiation.py  # Sections D & E
    ├── test_filtering.py                    # Section F: query filters
    ├── test_relationships.py                # Section G: categories/tasksof
    ├── test_side_effects.py                 # Section H: no side effects
    └── test_documented_vs_actual_bugs.py    # Bug pairs (BUG-001 to BUG-0011)
    └── test_command_line_queries.py         # curl-based command-line checks
```


**Note on `test_command_line_queries.py`:** every other file in this suite talks
to the API through the Python `requests` library. This file is different — it
shells out to the actual `curl` command via `subprocess` and parses its raw
output, to directly confirm (per the assignment's requirement) that command
line queries against the API function correctly, not just HTTP calls made
from Python code. Requires `curl` to be available on your system PATH
(pre-installed on Windows 10+, macOS, and most Linux distros).

## Design notes

- **Independence & ordering.** No test relies on hardcoded seed-data ids
  (e.g. "todo 1"). Every test that needs a todo/category/project creates its
  own via the `fresh_todo` / `fresh_category` / `fresh_project` fixtures in
  `conftest.py`, and cleans it up in teardown. This is what makes the suite
  safe to run in any order, including randomly.

- **Fails clearly if the service is down.** The `ensure_service_is_running`
  fixture in `conftest.py` runs once per session and aborts the whole run
  with a clear message if the API isn't reachable, rather than letting every
  test fail with a raw `ConnectionError` traceback.

- **Bug pairs use `xfail(strict=True)`.** Each bug has two tests: one
  asserting the *documented* behavior (marked `xfail`, since it is known to
  fail against the real API) and one asserting the *actual* observed
  behavior. `strict=True` means if the documented-behavior test ever starts
  passing (e.g. the API gets fixed), the suite will fail loudly, flagging
  that the test needs to be updated.

## Still to add

- JSON/XML payload generation is covered for todos; extend similarly for
  project/category endpoints if your group's scope includes them.
- Return-code sweep across all documented status codes, per the
  assignment's "Additional Unit Test Considerations" section.
