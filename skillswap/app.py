"""Flask web interface for SkillSwap (R1-R3, R5)."""

from flask import Flask, abort, redirect, render_template, request, url_for

from skillswap.core import Store, ValidationError


def create_app(data_path="data.json"):
    app = Flask(__name__)
    store = Store(data_path)

    def render_profile(profile_id, error=None, status=200):
        profile = store.get_profile(profile_id)
        if profile is None:
            abort(404)
        matches = store.find_matches(profile_id)
        page = render_template("profile.html", profile=profile, matches=matches, error=error)
        return page, status

    @app.get("/")
    def index():
        return render_template("index.html", profiles=store.list_profiles(), error=None)

    @app.post("/profiles")
    def create_profile():
        try:
            profile = store.create_profile(request.form.get("name", ""))
        except ValidationError as e:
            page = render_template("index.html", profiles=store.list_profiles(), error=str(e))
            return page, 400
        return redirect(url_for("profile", profile_id=profile["id"]))

    @app.get("/profile/<profile_id>")
    def profile(profile_id):
        return render_profile(profile_id)

    def add_service(profile_id, add):
        if store.get_profile(profile_id) is None:
            abort(404)
        try:
            add(profile_id, request.form.get("service", ""))
        except ValidationError as e:
            return render_profile(profile_id, error=str(e), status=400)
        return redirect(url_for("profile", profile_id=profile_id))

    @app.post("/profile/<profile_id>/offers")
    def add_offer(profile_id):
        return add_service(profile_id, store.add_offer)

    @app.post("/profile/<profile_id>/wants")
    def add_want(profile_id):
        return add_service(profile_id, store.add_want)

    return app
