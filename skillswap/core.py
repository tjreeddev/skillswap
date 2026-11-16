"""Pure SkillSwap logic: profiles, services, matching, and JSON storage."""

import json
from pathlib import Path


class ValidationError(ValueError):
    """Raised when user input is rejected."""


def normalize(text):
    """Trim, collapse internal whitespace, and lowercase (used for comparisons)."""
    return " ".join(text.split()).lower()


def _clean(text, what):
    cleaned = text.strip()
    if not cleaned:
        raise ValidationError(f"{what} cannot be blank.")
    return cleaned


class Store:
    """All profiles, loaded from and saved to one JSON file (R4)."""

    def __init__(self, path):
        self.path = Path(path)
        self.profiles = []
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.profiles = data.get("profiles", [])

    def _save(self):
        data = {"profiles": self.profiles}
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _find(self, profile_id):
        for p in self.profiles:
            if p["id"] == profile_id:
                return p
        return None

    @staticmethod
    def _copy(profile):
        return {**profile, "offers": list(profile["offers"]), "wants": list(profile["wants"])}

    def list_profiles(self):
        return [self._copy(p) for p in self.profiles]

    def get_profile(self, profile_id):
        p = self._find(profile_id)
        return self._copy(p) if p else None

    def create_profile(self, name):
        name = _clean(name, "Name")
        if any(normalize(p["name"]) == normalize(name) for p in self.profiles):
            raise ValidationError(f"A profile named {name!r} already exists.")
        next_id = max((int(p["id"]) for p in self.profiles), default=0) + 1
        profile = {"id": str(next_id), "name": name, "offers": [], "wants": []}
        self.profiles.append(profile)
        self._save()
        return self._copy(profile)

    def _add(self, profile_id, key, service):
        profile = self._find(profile_id)
        if profile is None:
            raise KeyError(profile_id)
        service = _clean(service, "Service")
        if normalize(service) not in {normalize(s) for s in profile[key]}:
            profile[key].append(service)
            self._save()

    def add_offer(self, profile_id, service):
        self._add(profile_id, "offers", service)

    def add_want(self, profile_id, service):
        self._add(profile_id, "wants", service)

    def find_matches(self, profile_id):
        """Other profiles that offer something this one wants AND want something it offers (R3)."""
        me = self._find(profile_id)
        if me is None:
            raise KeyError(profile_id)
        my_offers = {normalize(s) for s in me["offers"]}
        my_wants = {normalize(s) for s in me["wants"]}
        matches = []
        for other in self.profiles:
            if other["id"] == me["id"]:
                continue
            they_offer = [s for s in other["offers"] if normalize(s) in my_wants]
            they_want = [s for s in other["wants"] if normalize(s) in my_offers]
            if they_offer and they_want:
                matches.append(
                    {"name": other["name"], "they_offer": they_offer, "they_want": they_want}
                )
        return matches
