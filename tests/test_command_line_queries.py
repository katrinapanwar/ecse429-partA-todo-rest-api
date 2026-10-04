"""
confirms the API works correctly when queried from the actual command
line (curl), not just through the requests library like the rest of the
suite. runs curl as a real subprocess and checks its output.
"""

import json
import subprocess

from conftest import TODOS_URL, delete_todo


def run_curl(args):
    """Runs curl with the given extra args and returns (returncode, stdout)."""
    result = subprocess.run(
        ["curl", "-s", "-w", "\n%{http_code}"] + args,
        capture_output=True,
        text=True,
        timeout=10,
    )
    # the -w flag above appends the http status code on its own line at the end
    output_lines = result.stdout.rsplit("\n", 1)
    body = output_lines[0]
    status_code = int(output_lines[1]) if len(output_lines) > 1 and output_lines[1].strip().isdigit() else None
    return result.returncode, status_code, body


def test_curl_get_all_todos_returns_valid_json_and_200():
    returncode, status_code, body = run_curl([TODOS_URL])

    assert returncode == 0, "curl itself failed to run"
    assert status_code == 200
    parsed = json.loads(body)
    assert "todos" in parsed


def test_curl_create_todo_returns_201():
    returncode, status_code, body = run_curl([
        "-X", "POST", TODOS_URL,
        "-H", "Content-Type: application/json",
        "-d", '{"title": "curl command line test"}',
    ])

    try:
        assert returncode == 0
        assert status_code == 201
        parsed = json.loads(body)
        assert parsed["title"] == "curl command line test"
    finally:
        if status_code == 201:
            delete_todo(json.loads(body)["id"])


def test_curl_get_nonexistent_todo_returns_404():
    returncode, status_code, body = run_curl([f"{TODOS_URL}/999999"])

    assert returncode == 0
    assert status_code == 404


def test_curl_delete_todo_works():
    # create one via curl first so this test is self-contained
    _, create_status, create_body = run_curl([
        "-X", "POST", TODOS_URL,
        "-H", "Content-Type: application/json",
        "-d", '{"title": "curl delete test"}',
    ])
    assert create_status == 201
    todo_id = json.loads(create_body)["id"]

    returncode, status_code, _ = run_curl(["-X", "DELETE", f"{TODOS_URL}/{todo_id}"])

    assert returncode == 0
    assert status_code == 200

    # confirm it's actually gone, also via curl
    _, get_status, _ = run_curl([f"{TODOS_URL}/{todo_id}"])
    assert get_status == 404


def test_curl_malformed_json_returns_400():
    returncode, status_code, _ = run_curl([
        "-X", "POST", TODOS_URL,
        "-H", "Content-Type: application/json",
        "-d", '{"title": "missing closing brace"',
    ])

    assert returncode == 0
    assert status_code == 400
