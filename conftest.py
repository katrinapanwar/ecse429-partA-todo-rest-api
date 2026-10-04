import uuid

import pytest
import requests

BASE_URL = "http://localhost:4567"
TODOS_URL = f"{BASE_URL}/todos"
PROJECTS_URL = f"{BASE_URL}/projects"
CATEGORIES_URL = f"{BASE_URL}/categories"


# fails the whole run right away with a clear message if the server's not
# up, instead of every single test blowing up with a connection error
@pytest.fixture(scope="session", autouse=True)
def ensure_service_is_running():
    try:
        response = requests.get(TODOS_URL, timeout=3)
        if response.status_code >= 500:
            pytest.exit(f"API returned {response.status_code}, aborting run.", returncode=1)
    except requests.exceptions.ConnectionError:
        pytest.exit(
            f"Can't reach the API at {BASE_URL} - start it first with "
            "java -jar runTodoManagerRestAPI-1.5.5.jar",
            returncode=1,
        )


def unique_title(prefix="test todo"):
    # avoids collisions between tests when running out of order / repeatedly
    return f"{prefix} {uuid.uuid4().hex[:8]}"


def create_todo(title=None, done_status=None, description=None):
    payload = {"title": title if title is not None else unique_title()}
    if done_status is not None:
        payload["doneStatus"] = done_status
    if description is not None:
        payload["description"] = description
    return requests.post(TODOS_URL, json=payload)


def delete_todo(todo_id):
    return requests.delete(f"{TODOS_URL}/{todo_id}")


def get_todo(todo_id):
    return requests.get(f"{TODOS_URL}/{todo_id}")


def get_todo_fields(todo_id):
    # GET /todos/:id actually wraps the result in {"todos": [...]}, same as
    # the list endpoint - doesn't match the flat example in the docs. found
    # this the hard way when my asserts kept KeyError-ing on 'title'.
    response = get_todo(todo_id)
    response.raise_for_status()
    return response.json()["todos"][0]


def create_category(title=None, description=None):
    payload = {"title": title if title is not None else unique_title("category")}
    if description is not None:
        payload["description"] = description
    return requests.post(CATEGORIES_URL, json=payload)


def delete_category(category_id):
    return requests.delete(f"{CATEGORIES_URL}/{category_id}")


def create_project(title=None):
    payload = {"title": title if title is not None else unique_title("project")}
    return requests.post(PROJECTS_URL, json=payload)


def delete_project(project_id):
    return requests.delete(f"{PROJECTS_URL}/{project_id}")


@pytest.fixture
def fresh_todo():
    response = create_todo(
        title=unique_title(), done_status=False, description="created by fresh_todo fixture"
    )
    assert response.status_code == 201, f"couldn't set up test todo: {response.text}"
    todo = response.json()

    yield todo

    delete_todo(todo["id"])  # cleanup - ok if it's already gone


@pytest.fixture
def fresh_category():
    response = create_category(description="created by fresh_category fixture")
    assert response.status_code == 201
    category = response.json()

    yield category

    delete_category(category["id"])


@pytest.fixture
def fresh_project():
    response = create_project()
    assert response.status_code == 201
    project = response.json()

    yield project

    delete_project(project["id"])