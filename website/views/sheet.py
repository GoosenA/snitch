import os, requests

import google.auth.transport.requests
import google.oauth2.id_token

from flask import make_response, request, render_template, redirect
from flask.helpers import url_for
from models.session import Session
from models.user import User


class SheetView:
    RESULT_SUCCESS = "savedsuccess"
    RESULT_DELETESUCCESS = "deletesuccess"
    RESULT_FORMATSUCCESS = "formatsuccess"
    RESULT_FORMATFAILED = "formatfailed"
    GET_URL_WITH_RESULT = "/sheet?result={result}"

    def __init__(self):
        self.session = Session(request.cookies.get("session_id"))
        self.user = User(self.session.username)
        self.view_model = {
            "logged_in": self.session.logged_in,
            "username": self.user.username,
            "sheet_id": self.user.sheet_id,
            "service_acc": os.environ.get("SHEET_SERVICE_ACCOUNT", "setting-not-found"),
            "result": self.result(),
        }

    def get(self):
        response = make_response(render_template("sheet.html", vm=self.view_model))
        response.set_cookie("session_id", self.session.session_id, httponly=True, secure=True)
        return response

    def update(self):
        result = "error"  # default

        self.user.sheet_id = request.form.get("sheet_id", None)
        if not self.user.sheet_id:
            return redirect(self.GET_URL_WITH_RESULT.format(result=result))

        if not self.user.update_user():
            return redirect(self.GET_URL_WITH_RESULT.format(result=result))

        return redirect(self.GET_URL_WITH_RESULT.format(result=self.RESULT_SUCCESS))

    def delete(self):
        result = self.RESULT_DELETESUCCESS  # default
        self.user.sheet_id = None
        if not self.user.update_user():
            result = "error"
        return redirect(self.GET_URL_WITH_RESULT.format(result=result))

    def format(self):
        result = self.RESULT_FORMATSUCCESS  # default
        function_url = os.environ.get("URL_FORMAT_SHEET", None)
        if not function_url:
            result = "error"

        response = requests.post(
            function_url,
            json={"sheet_id": self.user.sheet_id},
            headers={"Authorization": f"Bearer {self.get_auth_token(function_url)}"},
        )
        if not (response.status_code == 200 and response.text == "success"):
            text = response.text.replace("\n", "")
            print(f"Sheet format status: {response.status_code}")
            print(f"Sheet format text: {text}")
            result = "error"
        return redirect(self.GET_URL_WITH_RESULT.format(result=result))

    def get_auth_token(self, service_url):

        auth_req = google.auth.transport.requests.Request()
        id_token = google.oauth2.id_token.fetch_id_token(auth_req, service_url)

        return id_token

    def result(self):
        result = request.args.get("result")
        if result is None:
            return None
        if result == self.RESULT_SUCCESS:
            return {"text": "Sheet ID successfully saved.", "format": "success"}
        if result == self.RESULT_DELETESUCCESS:
            return {"text": "Sheet ID successfully removed.", "format": "success"}
        if result == self.RESULT_FORMATSUCCESS:
            return {"text": "Sheet formatted successfully.", "format": "success"}
        if result == self.RESULT_FORMATFAILED:
            return {"text": "Sheet formatting failed.", "format": "warning"}
        return {"text": "Unknown result.", "format": "warning"}
