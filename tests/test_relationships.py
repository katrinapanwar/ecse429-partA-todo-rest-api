"""
Tests for linking/unlinking todos to categories and projects via
/todos/:id/categories and /todos/:id/tasksof. Matches the
"G. Relationships" section of our exploratory testing log.
"""

import requests

from conftest import TODOS_URL, create_todo, delete_todo


def test_new_todo_has_no_categories(fresh_todo):
    response = requests.get(f"{TODOS_URL}/{fresh_todo['id']}/categories")
    assert response.status_code == 200
    assert response.json()["categories"] == []


def test_head_todo_categories_returns_200_with_no_body(fresh_todo):
    response = requests.head(f"{TODOS_URL}/{fresh_todo['id']}/categories")
    assert response.status_code == 200
    assert response.text == ""


def test_link_todo_to_category(fresh_todo, fresh_category):
    response = requests.post(
        f"{TODOS_URL}/{fresh_todo['id']}/categories", json={"id": fresh_category["id"]}
    )
    assert response.status_code == 201

    linked = requests.get(f"{TODOS_URL}/{fresh_todo['id']}/categories").json()
    linked_ids = [c["id"] for c in linked["categories"]]
    assert fresh_category["id"] in linked_ids


def test_link_todo_to_nonexistent_category_returns_404(fresh_todo):
    response = requests.post(f"{TODOS_URL}/{fresh_todo['id']}/categories", json={"id": "999999"})
    assert response.status_code == 404


def test_remove_category_link(fresh_todo, fresh_category):
    requests.post(
        f"{TODOS_URL}/{fresh_todo['id']}/categories", json={"id": fresh_category["id"]}
    )
    response = requests.delete(
        f"{TODOS_URL}/{fresh_todo['id']}/categories/{fresh_category['id']}"
    )
    assert response.status_code == 200

    linked = requests.get(f"{TODOS_URL}/{fresh_todo['id']}/categories").json()
    assert linked["categories"] == []


def test_remove_category_link_twice_second_attempt_returns_404(fresh_todo, fresh_category):
    # invalid operation check: removing a link that's already been removed
    requests.post(
        f"{TODOS_URL}/{fresh_todo['id']}/categories", json={"id": fresh_category["id"]}
    )
    first = requests.delete(
        f"{TODOS_URL}/{fresh_todo['id']}/categories/{fresh_category['id']}"
    )
    assert first.status_code == 200

    second = requests.delete(
        f"{TODOS_URL}/{fresh_todo['id']}/categories/{fresh_category['id']}"
    )
    assert second.status_code == 404


def test_new_todo_has_no_tasksof(fresh_todo):
    response = requests.get(f"{TODOS_URL}/{fresh_todo['id']}/tasksof")
    assert response.status_code == 200
    assert response.json()["projects"] == []


def test_head_todo_tasksof_returns_200_with_no_body(fresh_todo):
    response = requests.head(f"{TODOS_URL}/{fresh_todo['id']}/tasksof")
    assert response.status_code == 200
    assert response.text == ""


def test_link_todo_to_project(fresh_todo, fresh_project):
    response = requests.post(
        f"{TODOS_URL}/{fresh_todo['id']}/tasksof", json={"id": fresh_project["id"]}
    )
    assert response.status_code == 201

    linked = requests.get(f"{TODOS_URL}/{fresh_todo['id']}/tasksof").json()
    linked_ids = [p["id"] for p in linked["projects"]]
    assert fresh_project["id"] in linked_ids


def test_link_todo_to_nonexistent_project_returns_404(fresh_todo):
    response = requests.post(f"{TODOS_URL}/{fresh_todo['id']}/tasksof", json={"id": "999999"})
    assert response.status_code == 404


def test_remove_tasksof_link(fresh_todo, fresh_project):
    requests.post(
        f"{TODOS_URL}/{fresh_todo['id']}/tasksof", json={"id": fresh_project["id"]}
    )
    response = requests.delete(
        f"{TODOS_URL}/{fresh_todo['id']}/tasksof/{fresh_project['id']}"
    )
    assert response.status_code == 200

    linked = requests.get(f"{TODOS_URL}/{fresh_todo['id']}/tasksof").json()
    assert linked["projects"] == []


def test_create_todo_with_category_embedded_in_creation_body(fresh_category):
    # confirmed working capability, not a bug: you can set relationships
    # directly in the POST /todos body instead of linking separately after
    response = requests.post(
        TODOS_URL,
        json={"title": "embedded relationship test", "categories": [{"id": fresh_category["id"]}]},
    )
    try:
        assert response.status_code == 201
        body = response.json()
        assert "categories" in body
        assert body["categories"][0]["id"] == fresh_category["id"]
    finally:
        delete_todo(response.json()["id"])