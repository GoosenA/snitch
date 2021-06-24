import datetime
from models.database import get_db
from uuid import uuid4


class Session:
    COLLECTION = "sessions"

    # Document fields
    session_id = None
    logged_in = False
    username = None
    created_date = None

    def __init__(self, session_id):
        self.session_id = session_id
        self.get_session_from_db()

    def get_session_from_db(self):
        db = get_db()
        self.logged_in = False
        if self.session_id is None:
            self.session_id = str(uuid4())  # Random, unique identifier

        doc_ref = db.collection(self.COLLECTION).document(document_id=self.session_id)
        doc = doc_ref.get()
        if doc.exists:
            session_data = doc.to_dict()
        else:
            self.create_new_session()
            return

        # Map user data
        self.username = session_data.get("username", None)
        self.created_date = session_data.get("created_data", None)
        if self.username:
            self.logged_in = True
        return

    def create_new_session(self):
        self.created_date = datetime.datetime.utcnow()
        return self.update_session()

    def update_session(self):
        # TODO: make more robust?
        db = get_db()

        session_data = {"session_id": self.session_id, "username": self.username, "created_date": self.created_date}
        db.collection(self.COLLECTION).document(self.session_id).set(session_data)
        return self.get_session_from_db()  # TODO: is this dodgy?

    def delete_session(self):
        db = get_db()

        doc_ref = db.collection(self.COLLECTION).document(document_id=self.session_id)
        doc = doc_ref.get()
        if doc.exists:
            doc.reference.delete()
        return
