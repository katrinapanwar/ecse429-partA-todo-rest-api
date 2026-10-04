"""
Tests for how the API validates todo fields on create and amend -- things
like rejecting an empty title, rejecting a non-boolean doneStatus, rejecting
unknown fields, and so on. Matches the "B. Validation" section of our
exploratory testing log (ECSE429_Exploratory_Testing_Log.xlsx).
"""

import requests

from conftest import TODOS_URL, delete_todo


def test_create_todo_with_no_title_is_rejected():
    response = requests.post(TODOS_URL, json={"doneStatus": True})
    assert response.status_code == 400


def test_create_todo_with_empty_title_is_rejected():
    response = requests.post(TODOS_URL, json={"title": ""})
    assert response.status_code == 400
    assert "title" in response.json()["errorMessages"][0].lower()


def test_create_todo_with_non_boolean_done_status_is_rejected():
    response = requests.post(TODOS_URL, json={"title": "x", "doneStatus": "maybe"})
    assert response.status_code == 400
    assert "BOOLEAN" in response.json()["errorMessages"][0]


def test_create_todo_with_undocumented_field_is_rejected():
    response = requests.post(TODOS_URL, json={"title": "x", "priority": "high"})
    assert response.status_code == 400
    assert "priority" in response.json()["errorMessages"][0]


def test_create_todo_with_client_supplied_id_is_rejected():
    response = requests.post(TODOS_URL, json={"title": "x", "id": "500"})
    assert response.status_code == 400


def test_amend_via_post_with_empty_title_is_rejected(fresh_todo):
    response = requests.post(f"{TODOS_URL}/{fresh_todo['id']}", json={"title": ""})
    assert response.status_code == 400


def test_amend_via_put_with_empty_title_is_rejected(fresh_todo):
    response = requests.put(f"{TODOS_URL}/{fresh_todo['id']}", json={"title": ""})
    assert response.status_code == 400
