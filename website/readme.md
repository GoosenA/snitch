# Deployment

- Navigate into the website folder. The one containing `main.py`
- Excute command: `gcloud app deploy --project=[PROJECT]`


# Local testing
  `gunicorn -b :8080 main:app`