"""
these are the pairs of tests for the bugs we found - one test shows what
the docs say should happen (marked xfail since it's known to fail), one
shows what the API actually does
"""

import pytest
import requests

from conftest import TODOS_URL, CATEGORIES_URL, PROJECTS_URL, create_todo, delete_todo, get_todo_fields


# BUG-001/002 - PUT wipes any field you don't include back to its default,
# even though the docs describe PUT the same way as POST (amend given
# fields). POST actually does leave other fields alone, PUT doesn't.

@pytest.mark.xfail(
    reason="docs say PUT should only touch the fields you send, but it "
           "resets everything else to default instead",
    strict=True,
)
def test_put_documented_behavior_FAILS_preserves_omitted_fields():
    create = create_todo(title="put doc test", done_status=True, description="keep me")
    todo_id = create.json()["id"]
    try:
        requests.put(f"{TODOS_URL}/{todo_id}", json={"title": "put doc test - amended"})
        current = get_todo_fields(todo_id)
        assert current["doneStatus"] in ("true", True)
        assert current["description"] == "keep me"
    finally:
        delete_todo(todo_id)


def test_put_actual_behavior_resets_omitted_fields_to_defaults():
    create = create_todo(title="put actual test", done_status=True, description="keep me")
    todo_id = create.json()["id"]
    try:
        requests.put(f"{TODOS_URL}/{todo_id}", json={"title": "put actual test - amended"})
        current = get_todo_fields(todo_id)
        assert current["doneStatus"] in ("false", False)
        assert current["description"] == ""
    finally:
        delete_todo(todo_id)


def test_post_actual_behavior_preserves_omitted_fields():
    # not a bug by itself, just confirms POST does the partial-update thing
    # the docs describe for both verbs - which is what makes PUT's behavior
    # inconsistent rather than just undocumented
    create = create_todo(title="post actual test", done_status=True, description="keep me")
    todo_id = create.json()["id"]
    try:
        requests.post(f"{TODOS_URL}/{todo_id}", json={"title": "post actual test - amended"})
        current = get_todo_fields(todo_id)
        assert current["doneStatus"] in ("true", True)
        assert current["description"] == "keep me"
    finally:
        delete_todo(todo_id)


def test_put_actual_behavior_clears_relationship_array_when_set_empty(fresh_todo, fresh_category):
    # extends BUG-001/002: the full-replace-vs-partial-update split isn't
    # just scalar fields (title/doneStatus/description), it applies to
    # relationship arrays too
    requests.post(f"{TODOS_URL}/{fresh_todo['id']}/categories", json={"id": fresh_category["id"]})
    requests.put(f"{TODOS_URL}/{fresh_todo['id']}", json={"title": fresh_todo["title"], "categories": []})

    categories = requests.get(f"{TODOS_URL}/{fresh_todo['id']}/categories").json()["categories"]
    assert categories == []


def test_post_actual_behavior_does_not_clear_relationship_array_when_set_empty(fresh_todo, fresh_category):
    requests.post(f"{TODOS_URL}/{fresh_todo['id']}/categories", json={"id": fresh_category["id"]})
    requests.post(f"{TODOS_URL}/{fresh_todo['id']}", json={"title": fresh_todo["title"], "categories": []})

    categories = requests.get(f"{TODOS_URL}/{fresh_todo['id']}/categories").json()["categories"]
    # POST leaves it alone, unlike PUT above - link should still be there
    assert len(categories) == 1
    assert categories[0]["id"] == fresh_category["id"]


# BUG-003 - title is supposed to be mandatory, but POST lets you amend a
# todo while leaving title out entirely and it just keeps the old title
# instead of rejecting the request

@pytest.mark.xfail(
    reason="title is mandatory per docs, expected this to be rejected same way PUT does",
    strict=True,
)
def test_post_amend_documented_behavior_FAILS_rejects_missing_title():
    create = create_todo(title="mandatory title test")
    todo_id = create.json()["id"]
    try:
        response = requests.post(f"{TODOS_URL}/{todo_id}", json={"doneStatus": True})
        assert response.status_code == 400
    finally:
        delete_todo(todo_id)


def test_post_amend_actual_behavior_silently_ignores_missing_title():
    create = create_todo(title="mandatory title test")
    todo_id = create.json()["id"]
    try:
        response = requests.post(f"{TODOS_URL}/{todo_id}", json={"doneStatus": True})
        current = get_todo_fields(todo_id)
        assert response.status_code == 200
        assert current["title"] == "mandatory title test"
    finally:
        delete_todo(todo_id)


# BUG-004 - title is documented as a string but sending a number for it
# works fine and gets stored as "123.0" instead of being rejected

@pytest.mark.xfail(
    reason="title should be STRING type per docs, expected a number to get rejected like "
           "doneStatus does when it's the wrong type",
    strict=True,
)
def test_title_type_documented_behavior_FAILS_rejects_numeric_title():
    response = requests.post(TODOS_URL, json={"title": 123})
    try:
        assert response.status_code == 400
    finally:
        if response.status_code == 201:
            delete_todo(response.json()["id"])


def test_title_type_actual_behavior_coerces_numeric_title():
    response = requests.post(TODOS_URL, json={"title": 123})
    try:
        assert response.status_code == 201
        assert response.json()["title"] == "123.0"  # coerced, not rejected
    finally:
        delete_todo(response.json()["id"])


# BUG-005 - filtering doesn't validate the same way the request body does.
# an unknown filter field just gets ignored, and an invalid doneStatus
# value in a filter returns an empty list instead of a 400 like it would on POST

@pytest.mark.xfail(
    reason="doneStatus is BOOLEAN per docs and is enforced on POST, expected the same "
           "validation to apply when it's used as a filter",
    strict=True,
)
def test_filter_documented_behavior_FAILS_validates_done_status_type():
    response = requests.get(TODOS_URL, params={"doneStatus": "notaboolean"})
    assert response.status_code == 400


def test_filter_actual_behavior_invalid_done_status_returns_empty_list():
    response = requests.get(TODOS_URL, params={"doneStatus": "notaboolean"})
    assert response.status_code == 200
    assert response.json()["todos"] == []


def test_filter_actual_behavior_unknown_field_is_silently_ignored():
    # same issue from a different angle - bad filter field name just gets
    # ignored and you get the full unfiltered list back
    all_todos = requests.get(TODOS_URL).json()["todos"]
    filtered = requests.get(TODOS_URL, params={"foo": "bar"})
    assert filtered.status_code == 200
    assert len(filtered.json()["todos"]) == len(all_todos)


# BUG-006 - posting the exact same category link twice returns 201 both
# times, like it created something new the second time, even though
# nothing actually changed

@pytest.mark.xfail(
    reason="a repeat link that changes nothing shouldn't return 201 again",
    strict=True,
)
def test_duplicate_link_documented_behavior_FAILS_second_post_is_not_201(fresh_todo, fresh_category):
    requests.post(f"{TODOS_URL}/{fresh_todo['id']}/categories", json={"id": fresh_category["id"]})
    second_response = requests.post(
        f"{TODOS_URL}/{fresh_todo['id']}/categories", json={"id": fresh_category["id"]}
    )
    assert second_response.status_code != 201


def test_duplicate_link_actual_behavior_returns_201_but_does_not_duplicate_data(
    fresh_todo, fresh_category
):
    requests.post(f"{TODOS_URL}/{fresh_todo['id']}/categories", json={"id": fresh_category["id"]})
    second_response = requests.post(
        f"{TODOS_URL}/{fresh_todo['id']}/categories", json={"id": fresh_category["id"]}
    )
    categories = requests.get(f"{TODOS_URL}/{fresh_todo['id']}/categories").json()["categories"]

    # 201 again, but it didn't actually duplicate anything server-side
    assert second_response.status_code == 201
    assert len(categories) == 1


# BUG-007 - GET /todos/:id doesn't match the docs' example at all. docs show
# a flat object, but it actually comes back wrapped in a "todos" array just
# like the list endpoint does. found this because my early tests kept
# KeyError-ing on "title".

@pytest.mark.xfail(
    reason="docs show a flat object for a single todo, not one wrapped in a todos array",
    strict=True,
)
def test_get_single_todo_documented_behavior_FAILS_flat_response_shape(fresh_todo):
    response = requests.get(f"{TODOS_URL}/{fresh_todo['id']}")
    body = response.json()
    assert "title" in body


def test_get_single_todo_actual_behavior_wrapped_in_todos_array(fresh_todo):
    response = requests.get(f"{TODOS_URL}/{fresh_todo['id']}")
    body = response.json()
    assert "todos" in body
    assert body["todos"][0]["title"] == fresh_todo["title"]


# BUG-008 - relationship endpoints don't check that the parent todo id
# actually exists. querying categories/tasksof for a todo id that doesn't
# exist returns real, unrelated data instead of a 404. same for HEAD.

@pytest.mark.xfail(
    reason="a relationship endpoint for a todo id that doesn't exist should return 404, "
           "same as GET /todos/:id does for a bad id",
    strict=True,
)
def test_categories_for_nonexistent_todo_documented_behavior_FAILS_404():
    response = requests.get(f"{TODOS_URL}/999999/categories")
    assert response.status_code == 404


def test_categories_for_nonexistent_todo_actual_behavior_returns_real_data():
    response = requests.get(f"{TODOS_URL}/999999/categories")
    assert response.status_code == 200
    # returns someone else's real category data instead of 404/empty
    assert len(response.json()["categories"]) > 0


@pytest.mark.xfail(
    reason="a relationship endpoint for a todo id that doesn't exist should return 404",
    strict=True,
)
def test_tasksof_for_nonexistent_todo_documented_behavior_FAILS_404():
    response = requests.get(f"{TODOS_URL}/999999/tasksof")
    assert response.status_code == 404


def test_tasksof_for_nonexistent_todo_actual_behavior_returns_real_data():
    response = requests.get(f"{TODOS_URL}/999999/tasksof")
    assert response.status_code == 200
    assert len(response.json()["projects"]) > 0


def test_head_categories_for_nonexistent_todo_actual_behavior_returns_200():
    # same underlying bug as above, confirmed on HEAD too
    response = requests.head(f"{TODOS_URL}/999999/categories")
    assert response.status_code == 200


def test_head_tasksof_for_nonexistent_todo_actual_behavior_returns_200():
    response = requests.head(f"{TODOS_URL}/999999/tasksof")
    assert response.status_code == 200


# BUG-009 - relationship POST endpoints can't parse a correctly-formatted
# XML id body. the exact same operation works fine as JSON.

@pytest.mark.xfail(
    reason="a well-formed XML id body should be accepted the same way JSON is",
    strict=True,
)
def test_xml_relationship_link_documented_behavior_FAILS_categories(fresh_todo, fresh_category):
    response = requests.post(
        f"{TODOS_URL}/{fresh_todo['id']}/categories",
        data=f"<id>{fresh_category['id']}</id>",
        headers={"Content-Type": "application/xml"},
    )
    assert response.status_code == 201


def test_xml_relationship_link_actual_behavior_categories_fails_to_parse(fresh_todo, fresh_category):
    response = requests.post(
        f"{TODOS_URL}/{fresh_todo['id']}/categories",
        data=f"<id>{fresh_category['id']}</id>",
        headers={"Content-Type": "application/xml"},
    )
    assert response.status_code == 400
    assert "IllegalStateException" in response.text


@pytest.mark.xfail(
    reason="a well-formed XML id body should be accepted the same way JSON is",
    strict=True,
)
def test_xml_relationship_link_documented_behavior_FAILS_tasksof(fresh_todo, fresh_project):
    response = requests.post(
        f"{TODOS_URL}/{fresh_todo['id']}/tasksof",
        data=f"<id>{fresh_project['id']}</id>",
        headers={"Content-Type": "application/xml"},
    )
    assert response.status_code == 201


def test_xml_relationship_link_actual_behavior_tasksof_fails_to_parse(fresh_todo, fresh_project):
    response = requests.post(
        f"{TODOS_URL}/{fresh_todo['id']}/tasksof",
        data=f"<id>{fresh_project['id']}</id>",
        headers={"Content-Type": "application/xml"},
    )
    assert response.status_code == 400
    assert "IllegalStateException" in response.text


# BUG-010 - linking a todo to a category only updates the relationship on
# the todo's side. the category side doesn't see it. todo-project linking
# (tasksof/tasks) works correctly both ways, so this is inconsistent.

@pytest.mark.xfail(
    reason="linking should show up on both sides, the way todo-project linking does",
    strict=True,
)
def test_category_todo_bidirectionality_documented_behavior_FAILS(fresh_todo, fresh_category):
    requests.post(f"{TODOS_URL}/{fresh_todo['id']}/categories", json={"id": fresh_category["id"]})
    reverse = requests.get(f"{CATEGORIES_URL}/{fresh_category['id']}/todos").json()
    todo_ids = [t["id"] for t in reverse["todos"]]
    assert fresh_todo["id"] in todo_ids


def test_category_todo_bidirectionality_actual_behavior_one_way_only(fresh_todo, fresh_category):
    requests.post(f"{TODOS_URL}/{fresh_todo['id']}/categories", json={"id": fresh_category["id"]})

    # works from the todo side
    forward = requests.get(f"{TODOS_URL}/{fresh_todo['id']}/categories").json()
    assert fresh_category["id"] in [c["id"] for c in forward["categories"]]

    # doesn't show up from the category side
    reverse = requests.get(f"{CATEGORIES_URL}/{fresh_category['id']}/todos").json()
    assert reverse["todos"] == []


def test_project_todo_bidirectionality_actual_behavior_works_both_ways(fresh_todo, fresh_project):
    # comparison case: unlike categories above, tasksof/tasks IS bidirectional
    requests.post(f"{TODOS_URL}/{fresh_todo['id']}/tasksof", json={"id": fresh_project["id"]})

    forward = requests.get(f"{TODOS_URL}/{fresh_todo['id']}/tasksof").json()
    assert fresh_project["id"] in [p["id"] for p in forward["projects"]]

    reverse = requests.get(f"{PROJECTS_URL}/{fresh_project['id']}/tasks").json()
    assert fresh_todo["id"] in [t["id"] for t in reverse["todos"]]

# BUG-011 - /todos/categories and /todos/tasksof (no :id segment at all)
# still return 200 with real data instead of a routing/validation error.
# same root cause as BUG-008, different malformed path.

@pytest.mark.xfail(
    reason="there's no documented /todos/categories route - with no todo id "
           "supplied at all, expected a 404 rather than real data",
    strict=True,
)
def test_undocumented_todos_categories_documented_behavior_FAILS():
    response = requests.get(f"{TODOS_URL}/categories")
    assert response.status_code == 404


def test_undocumented_todos_categories_actual_behavior_returns_unscoped_data():
    response = requests.get(f"{TODOS_URL}/categories")
    assert response.status_code == 200
    assert len(response.json()["categories"]) >= 1


@pytest.mark.xfail(
    reason="there's no documented /todos/tasksof route - with no todo id "
           "supplied at all, expected a 404 rather than real data",
    strict=True,
)
def test_undocumented_todos_tasksof_documented_behavior_FAILS():
    response = requests.get(f"{TODOS_URL}/tasksof")
    assert response.status_code == 404


def test_undocumented_todos_tasksof_actual_behavior_returns_unscoped_data():
    response = requests.get(f"{TODOS_URL}/tasksof")
    assert response.status_code == 200
    assert len(response.json()["projects"]) >= 1