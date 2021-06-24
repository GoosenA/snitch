import os
from flask import make_response, request, render_template
from models.session import Session


class CardCodeView:
    def __init__(self):
        self.session = Session(request.cookies.get("session_id"))
        self.view_model = {
            "logged_in": self.session.logged_in,
            "username": self.session.username,
            "function_url": os.environ.get("URL_PROCESS_TRANSACTION"),
        }

    def get_cardcode(self):
        response = make_response(render_template("cardcode.html", vm=self.view_model))
        response.set_cookie("session_id", self.session.session_id, httponly=True, secure=True)
        return response
