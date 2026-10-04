"""
Tests for filtering /todos with query parameters (?title=..., ?doneStatus=...),
including combined filters and whether matching is exact or partial.
Matches the "F. Filtering" section of our exploratory testing log.
"""

import requests

from conftest import TODOS_URL, create_todo, delete_todo, unique_title


def test_filter_by_exact_title_match(fresh_todo):
    response = requests.get(TODOS_URL, params={"title": fresh_todo["title"]})
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()["todos"]]
    assert fresh_todo["title"] in titles


def test_filter_by_done_status_true():
    create = create_todo(title=unique_title(), done_status=True)
    todo_id = create.json()["id"]
    try:
        response = requests.get(TODOS_URL, params={"doneStatus": "true"})
        ids = [t["id"] for t in response.json()["todos"]]
        assert todo_id in ids
    finally:
        delete_todo(todo_id)


def test_filter_with_no_matches_returns_empty_list():
    response = requests.get(TODOS_URL, params={"title": "no such todo exists " + unique_title()})
    assert response.status_code == 200
    assert response.json()["todos"] == []


def test_filter_combines_multiple_fields_with_and_logic():
    shared_title = unique_title("combo filter")
    match = create_todo(title=shared_title, done_status=False)
    non_match = create_todo(title=shared_title, done_status=True)
    try:
        response = requests.get(
            TODOS_URL, params={"title": shared_title, "doneStatus": "false"}
        )
        ids = [t["id"] for t in response.json()["todos"]]
        assert match.json()["id"] in ids
        assert non_match.json()["id"] not in ids
    finally:
        delete_todo(match.json()["id"])
        delete_todo(non_match.json()["id"])


def test_filter_is_exact_match_not_substring():
    create = create_todo(title=unique_title("exactmatchonly"))
    todo_id = create.json()["id"]
    try:
        # Query with only a substring of the real title.
        response = requests.get(TODOS_URL, params={"title": "exactmatchonly"})
        ids = [t["id"] for t in response.json()["todos"]]
        assert todo_id not in ids
    finally:
        delete_todo(todo_id)
