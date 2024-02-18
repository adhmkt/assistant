web: gunicorn -t 120 app:app
worker: celery -A app.celery worker --loglevel=info

