from flask import make_response, request, render_template, redirect
from flask.helpers import url_for
from models.session import Session
from models.user import User
from werkzeug.security import generate_password_hash


class RegisterView:
    RESULT_SUCCESS = "success"
    RESULT_USEREXISTS = "userexists"
    RESULT_CREATEFAILED = "createfailed"

    def __init__(self):
        self.session = Session(request.cookies.get("session_id"))
        self.view_model = {
            "logged_in": self.session.logged_in,
            "username": self.session.username,
            "result": self.result_string(),
        }

    def render(self):
        if request.method == "GET":
            return self.get()

        if request.method == "POST":
            return self.post()

    def get(self):
        response = make_response(render_template("register.html", vm=self.view_model))
        response.set_cookie("session_id", self.session.session_id, httponly=True, secure=True)
        return response

    def post(self):
        response_url = url_for(".register") + "?result={result}"
        result = self.RESULT_SUCCESS

        # TODO: Validate username requirements
        user = User(request.form["username"])
        if user.user_exists():
            result = self.RESULT_USEREXISTS
            return redirect(response_url.format(result=result))

        # TODO: Validate password requirements
        user.password = generate_password_hash(request.form["password"], salt_length=16)

        if not user.create_new_user():
            result = self.RESULT_CREATEFAILED

        return redirect(response_url.format(result=result))

    def result_string(self):
        result = request.args.get("result")
        if result is None:
            return None
        if result == self.RESULT_SUCCESS:
            return "registration_successful"
        if result == self.RESULT_USEREXISTS:
            return "Username already exists."
        if result == self.RESULT_CREATEFAILED:
            return "Failed to create user."
        return "Unknown error."
