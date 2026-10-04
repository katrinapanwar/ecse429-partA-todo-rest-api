"""
Tests confirming that an operation on one todo doesn't unexpectedly affect
other, unrelated todos or their linked projects/categories. Matches the
"H. Side Effects" section of our exploratory testing log.
"""

import requests

from conftest import PROJECTS_URL, TODOS_URL, create_todo, delete_todo, get_todo


def test_creating_a_todo_does_not_affect_unrelated_todos(fresh_todo):
    baseline = get_todo(fresh_todo["id"]).json()

    unrelated = create_todo()
    try:
        current = get_todo(fresh_todo["id"]).json()
        assert current == baseline
    finally:
        delete_todo(unrelated.json()["id"])


def test_deleting_a_todo_does_not_delete_its_linked_project(fresh_todo, fresh_project):
    requests.post(
        f"{TODOS_URL}/{fresh_todo['id']}/tasksof", json={"id": fresh_project["id"]}
    )
    baseline = requests.get(f"{PROJECTS_URL}/{fresh_project['id']}").json()

    delete_response = requests.delete(f"{TODOS_URL}/{fresh_todo['id']}")
    assert delete_response.status_code == 200

    project_response = requests.get(f"{PROJECTS_URL}/{fresh_project['id']}")
    assert project_response.status_code == 200
    # go further than "it still exists" - confirm its own fields weren't
    # touched either, beyond just dropping the deleted todo from its tasks
    current = project_response.json()
    assert current["projects"][0]["title"] == baseline["projects"][0]["title"]
    assert current["projects"][0]["completed"] == baseline["projects"][0]["completed"]
    assert current["projects"][0]["active"] == baseline["projects"][0]["active"]


def test_deleting_a_todo_removes_it_from_linked_projects_task_list(fresh_todo, fresh_project):
    requests.post(
        f"{TODOS_URL}/{fresh_todo['id']}/tasksof", json={"id": fresh_project["id"]}
    )

    requests.delete(f"{TODOS_URL}/{fresh_todo['id']}")

    tasks = requests.get(f"{PROJECTS_URL}/{fresh_project['id']}/tasks").json()["todos"]
    task_ids = [t["id"] for t in tasks]
    assert fresh_todo["id"] not in task_ids


def test_deleting_a_todo_does_not_affect_unrelated_todos(fresh_todo):
    other = create_todo()
    baseline = get_todo(other.json()["id"]).json()

    requests.delete(f"{TODOS_URL}/{fresh_todo['id']}")

    try:
        current = get_todo(other.json()["id"]).json()
        assert current == baseline
    finally:
        delete_todo(other.json()["id"])