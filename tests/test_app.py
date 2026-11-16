"""Web-level tests for skillswap.app using Flask's test client.

Expected interface (from spec.md):
    create_app(data_path=...) -> Flask app
    GET  /                       home: create form + list of profiles
    POST /profiles               form field "name"    -> redirect to /profile/<id>
    GET  /profile/<id>           profile page (404 if unknown)
    POST /profile/<id>/offers    form field "service" -> redirect back
    POST /profile/<id>/wants     form field "service" -> redirect back
"""

import importlib.util

from conftest import reload_store


def create(client, name):
    """Create a profile through the web UI and return its id."""
    resp = client.post("/profiles", data={"name": name})
    assert resp.status_code in (302, 303)
    location = resp.headers["Location"]
    assert "/profile/" in location
    return location.rstrip("/").rsplit("/", 1)[-1]


def add(client, pid, kind, service):
    return client.post(f"/profile/{pid}/{kind}", data={"service": service})


# ---------------------------------------------------------------- R1


def test_R1_home_shows_create_profile_form(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"<form" in resp.data
    assert b'name="name"' in resp.data


def test_R1_create_profile_redirects_to_its_page(client):
    pid = create(client, "Ana")
    resp = client.get(f"/profile/{pid}")
    assert resp.status_code == 200
    assert b"Ana" in resp.data


def test_R1_existing_profiles_are_listed_and_choosable(client):
    ana = create(client, "Ana")
    ben = create(client, "Ben")
    html = client.get("/").get_data(as_text=True)
    assert "Ana" in html and "Ben" in html
    assert f"/profile/{ana}" in html
    assert f"/profile/{ben}" in html


def test_R1_blank_name_is_rejected(client, data_path):
    resp = client.post("/profiles", data={"name": "   "})
    assert resp.status_code not in (302, 303)
    assert reload_store(data_path).list_profiles() == []


def test_R1_duplicate_name_is_rejected(client, data_path):
    create(client, "Ana")
    resp = client.post("/profiles", data={"name": " ANA "})
    assert resp.status_code not in (302, 303)
    assert len(reload_store(data_path).list_profiles()) == 1


def test_R1_unknown_profile_returns_404(client):
    assert client.get("/profile/does-not-exist").status_code == 404


# ---------------------------------------------------------------- R2


def test_R2_profile_page_has_offer_and_want_forms(client):
    pid = create(client, "Ana")
    html = client.get(f"/profile/{pid}").get_data(as_text=True)
    assert f"/profile/{pid}/offers" in html
    assert f"/profile/{pid}/wants" in html
    assert 'name="service"' in html


def test_R2_added_offer_and_want_are_saved_and_shown(client, data_path):
    pid = create(client, "Ana")
    r1 = add(client, pid, "offers", "Logo design")
    r2 = add(client, pid, "wants", "Tax help")
    assert r1.status_code in (302, 303)
    assert r2.status_code in (302, 303)

    p = reload_store(data_path).get_profile(pid)
    assert p["offers"] == ["Logo design"]
    assert p["wants"] == ["Tax help"]

    html = client.get(f"/profile/{pid}").get_data(as_text=True)
    assert "Logo design" in html and "Tax help" in html


def test_R2_blank_service_is_rejected(client, data_path):
    pid = create(client, "Ana")
    r1 = add(client, pid, "offers", "  ")
    r2 = add(client, pid, "wants", "")
    assert r1.status_code not in (302, 303)
    assert r2.status_code not in (302, 303)
    p = reload_store(data_path).get_profile(pid)
    assert p["offers"] == [] and p["wants"] == []


def test_R2_adding_service_to_unknown_profile_returns_404(client):
    assert add(client, "does-not-exist", "offers", "Logo design").status_code == 404
    assert add(client, "does-not-exist", "wants", "Tax help").status_code == 404


# ---------------------------------------------------------------- R3


def test_R3_profile_page_shows_match_with_matching_services(client):
    ana = create(client, "Ana")
    add(client, ana, "offers", "Logo design")
    add(client, ana, "wants", "Tax help")
    ben = create(client, "Ben")
    add(client, ben, "offers", "Tax help")
    add(client, ben, "offers", "Plumbing")
    add(client, ben, "wants", "Logo design")

    html = client.get(f"/profile/{ana}").get_data(as_text=True)
    assert "Ben" in html
    assert "Tax help" in html
    assert "Plumbing" not in html  # Ben offers it, but Ana doesn't want it


def test_R3_non_match_is_not_shown(client):
    ana = create(client, "Ana")
    add(client, ana, "offers", "Logo design")
    add(client, ana, "wants", "Tax help")
    cara = create(client, "Cara")
    add(client, cara, "offers", "Tax help")
    add(client, cara, "wants", "Plumbing")

    html = client.get(f"/profile/{ana}").get_data(as_text=True)
    assert "Cara" not in html


# ---------------------------------------------------------------- R4


def test_R4_data_survives_app_restart(data_path):
    from skillswap.app import create_app

    first = create_app(data_path=data_path).test_client()
    pid = create(first, "Ana")
    add(first, pid, "offers", "Logo design")
    add(first, pid, "wants", "Tax help")

    second = create_app(data_path=data_path).test_client()
    assert "Ana" in second.get("/").get_data(as_text=True)
    html = second.get(f"/profile/{pid}").get_data(as_text=True)
    assert "Logo design" in html and "Tax help" in html


def test_R4_app_starts_with_missing_data_file(tmp_path):
    from skillswap.app import create_app

    client = create_app(data_path=tmp_path / "missing.json").test_client()
    assert client.get("/").status_code == 200


# ---------------------------------------------------------------- R5


def test_R5_app_factory_serves_html_home_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.mimetype == "text/html"


def test_R5_package_is_runnable_with_python_dash_m():
    # `uv run python -m skillswap` requires skillswap/__main__.py.
    assert importlib.util.find_spec("skillswap.__main__") is not None
