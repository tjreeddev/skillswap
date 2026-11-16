"""Unit tests for skillswap.core (pure logic, no Flask).

Expected interface (from spec.md / CLAUDE.md):
    normalize(s) -> str
    ValidationError (subclass of ValueError)
    Store(path)
        .create_profile(name) -> profile dict {"id", "name", "offers", "wants"}
        .list_profiles() -> list of profile dicts
        .get_profile(id) -> profile dict or None
        .add_offer(id, service)
        .add_want(id, service)
        .find_matches(id) -> list of {"name", "they_offer", "they_want"}
"""

import json

import pytest

from conftest import reload_store


def validation_error():
    from skillswap.core import ValidationError

    return ValidationError


def make(store, name, offers=(), wants=()):
    p = store.create_profile(name)
    for s in offers:
        store.add_offer(p["id"], s)
    for s in wants:
        store.add_want(p["id"], s)
    return p["id"]


# ---------------------------------------------------------------- normalize


def test_normalize_trims_collapses_and_lowercases():  # supports R1, R2, R3
    from skillswap.core import normalize

    assert normalize("  Logo   Design ") == "logo design"


# ---------------------------------------------------------------- R1


def test_R1_create_profile_returns_profile_with_name_and_empty_lists(store):
    p = store.create_profile("Ana")
    assert p["name"] == "Ana"
    assert p["offers"] == []
    assert p["wants"] == []
    assert p["id"]


def test_R1_created_profile_is_listed_and_can_be_chosen(store):
    p = store.create_profile("Ana")
    assert [x["name"] for x in store.list_profiles()] == ["Ana"]
    assert store.get_profile(p["id"])["name"] == "Ana"


def test_R1_profile_name_is_trimmed(store):
    p = store.create_profile("  Ana  ")
    assert p["name"] == "Ana"


def test_R1_profiles_get_unique_ids(store):
    a = store.create_profile("Ana")
    b = store.create_profile("Ben")
    assert a["id"] != b["id"]


@pytest.mark.parametrize("name", ["", "   "])
def test_R1_blank_name_is_rejected(store, name):
    with pytest.raises(validation_error()):
        store.create_profile(name)
    assert store.list_profiles() == []


def test_R1_duplicate_name_ignoring_case_and_space_is_rejected(store):
    store.create_profile("Ana Lee")
    with pytest.raises(validation_error()):
        store.create_profile("  ana   LEE ")
    assert len(store.list_profiles()) == 1


def test_R1_unknown_profile_id_returns_none(store):
    assert store.get_profile("does-not-exist") is None


# ---------------------------------------------------------------- R2


def test_R2_add_offer_goes_to_offers_only(store):
    pid = store.create_profile("Ana")["id"]
    store.add_offer(pid, "Logo design")
    p = store.get_profile(pid)
    assert p["offers"] == ["Logo design"]
    assert p["wants"] == []


def test_R2_add_want_goes_to_wants_only(store):
    pid = store.create_profile("Ana")["id"]
    store.add_want(pid, "Tax help")
    p = store.get_profile(pid)
    assert p["wants"] == ["Tax help"]
    assert p["offers"] == []


def test_R2_service_is_stored_trimmed_with_original_case(store):
    pid = store.create_profile("Ana")["id"]
    store.add_offer(pid, "  Logo Design  ")
    assert store.get_profile(pid)["offers"] == ["Logo Design"]


@pytest.mark.parametrize("service", ["", "   "])
def test_R2_blank_service_is_rejected(store, service):
    pid = store.create_profile("Ana")["id"]
    with pytest.raises(validation_error()):
        store.add_offer(pid, service)
    with pytest.raises(validation_error()):
        store.add_want(pid, service)
    p = store.get_profile(pid)
    assert p["offers"] == [] and p["wants"] == []


def test_R2_repeated_service_in_same_list_is_stored_once(store):
    pid = store.create_profile("Ana")["id"]
    store.add_offer(pid, "Logo design")
    store.add_offer(pid, "  LOGO   design ")
    store.add_want(pid, "Tax help")
    store.add_want(pid, "tax HELP")
    p = store.get_profile(pid)
    assert p["offers"] == ["Logo design"]
    assert p["wants"] == ["Tax help"]


def test_R2_same_service_may_be_in_both_lists(store):
    pid = store.create_profile("Ana")["id"]
    store.add_offer(pid, "Tutoring")
    store.add_want(pid, "Tutoring")
    p = store.get_profile(pid)
    assert p["offers"] == ["Tutoring"] and p["wants"] == ["Tutoring"]


# ---------------------------------------------------------------- R3


def test_R3_mutual_match_is_listed_with_matching_services(store):
    ana = make(store, "Ana", offers=["Logo design", "Baking"], wants=["Tax help"])
    make(store, "Ben", offers=["Tax help", "Plumbing"], wants=["Logo design"])

    matches = store.find_matches(ana)
    assert len(matches) == 1
    m = matches[0]
    assert m["name"] == "Ben"
    assert set(m["they_offer"]) == {"Tax help"}
    assert set(m["they_want"]) == {"Logo design"}


def test_R3_match_is_symmetric(store):
    make(store, "Ana", offers=["Logo design"], wants=["Tax help"])
    ben = make(store, "Ben", offers=["Tax help"], wants=["Logo design"])
    assert [m["name"] for m in store.find_matches(ben)] == ["Ana"]


def test_R3_one_direction_only_is_not_a_match(store):
    ana = make(store, "Ana", offers=["Logo design"], wants=["Tax help"])
    # Cara offers what Ana wants but wants nothing Ana offers.
    make(store, "Cara", offers=["Tax help"], wants=["Plumbing"])
    # Dan wants what Ana offers but offers nothing Ana wants.
    make(store, "Dan", offers=["Gardening"], wants=["Logo design"])
    assert store.find_matches(ana) == []


def test_R3_profile_never_matches_itself(store):
    ana = make(store, "Ana", offers=["Tutoring"], wants=["Tutoring"])
    assert store.find_matches(ana) == []


def test_R3_profile_with_no_services_has_no_matches(store):
    ana = make(store, "Ana")
    make(store, "Ben", offers=["Tax help"], wants=["Logo design"])
    assert store.find_matches(ana) == []


def test_R3_matching_ignores_case_and_extra_spaces(store):
    ana = make(store, "Ana", offers=["Logo Design"], wants=["Tax Help"])
    make(store, "Ben", offers=["  tax   help "], wants=["LOGO design"])
    assert [m["name"] for m in store.find_matches(ana)] == ["Ben"]


def test_R3_substring_does_not_match(store):
    ana = make(store, "Ana", offers=["Logo design"], wants=["Tax help"])
    make(store, "Ben", offers=["Tax"], wants=["Logo"])
    assert store.find_matches(ana) == []


def test_R3_multiple_matches_are_all_listed(store):
    ana = make(store, "Ana", offers=["Logo design"], wants=["Tax help"])
    make(store, "Ben", offers=["Tax help"], wants=["Logo design"])
    make(store, "Cara", offers=["Tax help"], wants=["Logo design"])
    make(store, "Dan", offers=["Plumbing"], wants=["Baking"])
    assert {m["name"] for m in store.find_matches(ana)} == {"Ben", "Cara"}


# ---------------------------------------------------------------- R4


def test_R4_profiles_and_services_survive_reload(store, data_path):
    pid = make(store, "Ana", offers=["Logo design"], wants=["Tax help"])

    reloaded = reload_store(data_path)
    p = reloaded.get_profile(pid)
    assert p["name"] == "Ana"
    assert p["offers"] == ["Logo design"]
    assert p["wants"] == ["Tax help"]


def test_R4_every_change_is_saved_immediately(store, data_path):
    pid = store.create_profile("Ana")["id"]
    assert reload_store(data_path).get_profile(pid) is not None
    store.add_offer(pid, "Logo design")
    assert reload_store(data_path).get_profile(pid)["offers"] == ["Logo design"]
    store.add_want(pid, "Tax help")
    assert reload_store(data_path).get_profile(pid)["wants"] == ["Tax help"]


def test_R4_file_uses_documented_json_format(store, data_path):
    make(store, "Ana", offers=["Logo design"], wants=["Tax help"])
    data = json.loads(data_path.read_text(encoding="utf-8"))
    assert list(data.keys()) == ["profiles"]
    (p,) = data["profiles"]
    assert set(p.keys()) == {"id", "name", "offers", "wants"}
    assert p["name"] == "Ana"
    assert p["offers"] == ["Logo design"]
    assert p["wants"] == ["Tax help"]


def test_R4_missing_file_starts_empty_without_crashing(tmp_path):
    from skillswap.core import Store

    s = Store(tmp_path / "missing.json")
    assert s.list_profiles() == []


def test_R4_duplicate_check_still_applies_after_reload(store, data_path):
    store.create_profile("Ana")
    with pytest.raises(validation_error()):
        reload_store(data_path).create_profile("ana")
