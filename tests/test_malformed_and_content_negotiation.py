"""
Tests for malformed request bodies (broken JSON/XML, wrong Content-Type)
and for content negotiation -- sending/receiving todos as JSON vs XML via
the Content-Type and Accept headers. Matches the "D. Malformed Requests"
and "E. Content Negotiation" sections of our exploratory testing log.
"""

import requests

from conftest import TODOS_URL, delete_todo


def test_malformed_json_body_returns_400_not_server_error():
    response = requests.post(
        TODOS_URL,
        data='{"title": "missing closing brace"',  # deliberately malformed
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    assert response.status_code < 500
    # confirms the server gave a real, well-formed error response rather
    # than an empty body or a bare status code
    assert "errorMessages" in response.json()


def test_malformed_xml_body_returns_400_not_server_error():
    response = requests.post(
        TODOS_URL,
        data="<todo><title>unclosed",  # deliberately malformed
        headers={"Content-Type": "application/xml"},
    )
    assert response.status_code == 400
    assert response.status_code < 500
    assert "errorMessages" in response.json()


def test_content_type_json_but_body_is_xml_returns_400():
    response = requests.post(
        TODOS_URL,
        data="<todo><title>mismatch test</title></todo>",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    assert "errorMessages" in response.json()


def test_no_content_type_header_defaults_to_json():
    """Docs state the API 'will accept json by default'."""
    response = requests.post(
        TODOS_URL,
        data='{"title": "no content-type header test"}',
        headers={"Content-Type": ""},
    )
    try:
        assert response.status_code == 201
    finally:
        if response.status_code == 201:
            delete_todo(response.json()["id"])


def test_json_request_with_xml_accept_returns_xml():
    response = requests.post(
        TODOS_URL,
        json={"title": "accept xml test"},
        headers={"Accept": "application/xml"},
    )
    try:
        assert response.status_code == 201
        assert response.headers["Content-Type"].startswith("application/xml")
        assert response.text.strip().startswith("<todo>")
    finally:
        # Response is XML; extract id with a light parse for cleanup.
        import re
        match = re.search(r"<id>(\d+)</id>", response.text)
        if match:
            delete_todo(match.group(1))


def test_xml_request_with_json_accept_returns_json():
    xml_body = "<todo><title>xml in json out test</title></todo>"
    response = requests.post(
        TODOS_URL,
        data=xml_body,
        headers={"Content-Type": "application/xml", "Accept": "application/json"},
    )
    try:
        assert response.status_code == 201
        assert response.headers["Content-Type"].startswith("application/json")
        body = response.json()
        assert body["title"] == "xml in json out test"
    finally:
        delete_todo(response.json()["id"])


def test_get_todos_list_with_xml_accept_wraps_all_items():
    response = requests.get(TODOS_URL, headers={"Accept": "application/xml"})
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/xml")
    assert response.text.strip().startswith("<todos>")