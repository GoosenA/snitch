import os
from flask import make_response, request, render_template
from models.session import Session


class AppScriptView:
    def __init__(self):
        self.session = Session(request.cookies.get("session_id"))
        self.view_model = {
            "logged_in": self.session.logged_in,
            "username": self.session.username,
        }

    def get_app_script(self):
        response = make_response(render_template("appscript.html", vm=self.view_model))
        response.set_cookie("session_id", self.session.session_id, httponly=True, secure=True)
        return response
