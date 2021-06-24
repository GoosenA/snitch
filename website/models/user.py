import datetime
from models.database import get_db


class User:
    COLLECTION = "users"

    exists = None

    # Document fields
    username = None
    password = None
    created_date = None
    sheet_id = None

    def __init__(self, username):
        # TODO: Validate username requirements
        self.username = username
        self.get_user_from_db()

    def get_user_from_db(self):
        db = get_db()
        self.exists = False

        doc_ref = db.collection(self.COLLECTION).document(document_id=self.username)
        doc = doc_ref.get()
        if doc.exists:
            user_data = doc.to_dict()
        else:
            return False

        # Map user data
        self.username = user_data.get("username", None)
        self.password = user_data.get("password", None)
        self.created_date = user_data.get("created_date", None)
        self.sheet_id = user_data.get("sheet_id", None)

        # Validate required fields
        if self.username and self.password:
            self.exists = True

        return self.exists

    def create_new_user(self):
        if self.user_exists():
            return False

        self.created_date = datetime.datetime.utcnow()
        return self.update_user()

    def update_user(self):
        db = get_db()

        user_data = {
            "username": self.username,
            "password": self.password,
            "created_date": self.created_date,
            "sheet_id": self.sheet_id,
        }
        db.collection(self.COLLECTION).document(self.username).set(user_data)
        return self.get_user_from_db()  # TODO: is this dodgy?

    def user_exists(self):
        if self.exists is None:
            self.get_user_from_db()
        return self.exists
