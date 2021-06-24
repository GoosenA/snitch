from flask import make_response, request, render_template
from models.session import Session


class HomeView:
    def __init__(self):
        self.session = Session(request.cookies.get("session_id"))
        self.view_model = {
            "logged_in": self.session.logged_in,
            "username": self.session.username,
        }

    def get_home(self):
        response = make_response(render_template("home.html", vm=self.view_model))
        response.set_cookie(
            "session_id", self.session.session_id, httponly=True, secure=True
        )  # TODO: make cookies expire
        return response
