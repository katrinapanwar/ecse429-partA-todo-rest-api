"""
Basic create/read/update/delete behavior for /todos -- GET, POST, PUT,
DELETE, HEAD. Matches the "A. Core CRUD" section of our exploratory
testing log (ECSE429_Exploratory_Testing_Log.xlsx).
"""

import requests

from conftest import TODOS_URL, create_todo, delete_todo, get_todo, get_todo_fields, unique_title


def test_get_all_todos_returns_200():
    response = requests.get(TODOS_URL)
    assert response.status_code == 200
    body = response.json()
    assert "todos" in body


def test_get_single_todo_by_valid_id(fresh_todo):
    response = get_todo(fresh_todo["id"])
    assert response.status_code == 200
    # Note: GET /todos/:id wraps its result in a "todos" array, same as the
    # list endpoint -- unlike the flat single-object example shown in docs.
    assert response.json()["todos"][0]["title"] == fresh_todo["title"]


def test_get_todo_by_nonexistent_id_returns_404():
    response = get_todo("999999")
    assert response.status_code == 404
    assert "999999" in response.json()["errorMessages"][0]


def test_create_todo_valid_full_payload():
    title = unique_title()
    response = create_todo(title=title, done_status=True, description="full payload")
    try:
        assert response.status_code == 201
        body = response.json()
        assert body["title"] == title
        assert body["doneStatus"] == "true" or body["doneStatus"] is True
        assert body["description"] == "full payload"
        assert "id" in body and body["id"]
    finally:
        delete_todo(response.json()["id"])


def test_create_todo_title_only_defaults_applied():
    response = create_todo(title=unique_title())
    try:
        assert response.status_code == 201
        body = response.json()
        # Documented default behavior observed during exploratory testing:
        # doneStatus defaults to false, description defaults to empty string.
        assert body["doneStatus"] in ("false", False)
        assert body["description"] == ""
    finally:
        delete_todo(response.json()["id"])


def test_delete_todo_removes_it(fresh_todo):
    delete_response = delete_todo(fresh_todo["id"])
    assert delete_response.status_code == 200

    get_response = get_todo(fresh_todo["id"])
    assert get_response.status_code == 404


def test_head_todos_returns_200_with_no_body():
    response = requests.head(TODOS_URL)
    assert response.status_code == 200
    assert response.text == ""


def test_head_single_todo_returns_200_with_no_body(fresh_todo):
    response = requests.head(f"{TODOS_URL}/{fresh_todo['id']}")
    assert response.status_code == 200
    assert response.text == ""