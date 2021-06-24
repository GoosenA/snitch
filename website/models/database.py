from flask import g
from google.cloud import firestore


def get_db():
    if "db" not in g:
        g.db = firestore.Client()
    return g.db
