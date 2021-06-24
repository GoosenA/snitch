from flask import Flask, request
from flask.helpers import url_for
from werkzeug.utils import redirect

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    from views.home import HomeView

    if request.method == "GET":
        return HomeView().get_home()


@app.route("/appscript", methods=["GET"])
def appscript():
    from views.appscript import AppScriptView

    return AppScriptView().get_app_script()


@app.route("/cardcode", methods=["GET"])
def cardcode():
    from views.cardcode import CardCodeView

    return CardCodeView().get_cardcode()


@app.route("/login", methods=["GET", "POST"])
def login():
    from views.login import LoginView

    if request.method == "GET":
        return LoginView().get_login()

    if request.method == "POST":
        return LoginView().post_login()


@app.route("/logout", methods=["GET"])
def logout():
    from models.session import Session

    session = Session(request.cookies.get("session_id"))
    session.delete_session()
    return redirect(url_for(".home"))


@app.route("/sheet", methods=["GET"])
@app.route("/sheet/update", methods=["POST"])
@app.route("/sheet/delete", methods=["POST"])
@app.route("/sheet/format", methods=["POST"])
def sheet():
    from views.sheet import SheetView

    if request.path == "/sheet/update":
        return SheetView().update()
    if request.path == "/sheet/delete":
        return SheetView().delete()
    if request.path == "/sheet/format":
        return SheetView().format()
    return SheetView().get()


@app.route("/register", methods=["GET", "POST"])
def register():
    from views.register import RegisterView

    return RegisterView().render()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
