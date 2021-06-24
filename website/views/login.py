from flask import make_response, request, render_template, redirect, url_for
from models.session import Session
from models.user import User
from werkzeug.security import check_password_hash


class LoginView:
    RESULT_INVALIDCREDENTIALS = "invalidcredentials"

    def __init__(self):
        self.session = Session(request.cookies.get("session_id"))
        self.view_model = {
            "logged_in": self.session.logged_in,
            "username": self.session.username,
            "result": self.result_string(),
        }

    def get_login(self):
        if self.session.logged_in:
            return redirect(url_for(".home"))

        response = make_response(render_template("login.html", vm=self.view_model))
        response.set_cookie("session_id", self.session.session_id, httponly=True, secure=True)
        return response

    def post_login(self):
        if self.session.logged_in:
            return redirect(url_for(".home"))

        fail_response_url = url_for(".login") + f"?result={self.RESULT_INVALIDCREDENTIALS}"

        user = User(request.form["username"])
        if not user.user_exists():
            return redirect(fail_response_url)

        if check_password_hash(user.password, request.form["password"]):
            self.session.username = user.username
            self.session.update_session()
            return redirect(url_for(".home"))

        return redirect(fail_response_url)

    def result_string(self):
        result = request.args.get("result")
        if result is None:
            return None
        if result == self.RESULT_INVALIDCREDENTIALS:
            return "Invalid credentials."
        return "Unknown error."
