"""
Edge cases around how the API handles todo ids in the URL -- ids that don't
exist, non-numeric ids, negative/zero ids, deleting something twice.
Matches the "C. ID / Addressing" section of our exploratory testing log.
"""

import requests

from conftest import TODOS_URL, delete_todo


def test_put_to_nonexistent_id_returns_404():
    response = requests.put(f"{TODOS_URL}/999999", json={"title": "x"})
    assert response.status_code == 404
    # confirms the operation was actually refused for the right reason, not
    # just that *some* 404 came back
    assert "999999" in response.json()["errorMessages"][0]


def test_post_to_nonexistent_id_returns_404():
    response = requests.post(f"{TODOS_URL}/999999", json={"title": "x"})
    assert response.status_code == 404
    assert "999999" in response.json()["errorMessages"][0]


def test_delete_already_deleted_todo_returns_404(fresh_todo):
    first = delete_todo(fresh_todo["id"])
    assert first.status_code == 200

    second = delete_todo(fresh_todo["id"])
    assert second.status_code == 404
    assert fresh_todo["id"] in second.json()["errorMessages"][0]


def test_non_numeric_id_returns_404_not_crash():
    response = requests.get(f"{TODOS_URL}/abc")
    assert response.status_code == 404
    # confirmed via actual test run: GET uses this message for a non-numeric id
    assert "abc" in response.json()["errorMessages"][0]


def test_negative_id_returns_404_not_crash():
    response = requests.get(f"{TODOS_URL}/-1")
    assert response.status_code == 404
    assert "errorMessages" in response.json()


def test_zero_id_returns_404_not_crash():
    response = requests.get(f"{TODOS_URL}/0")
    assert response.status_code == 404
    assert "errorMessages" in response.json()