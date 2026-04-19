"""
wsgi.py
-------
WSGI entry point for production servers (Gunicorn, uWSGI, etc.)
This file resolves the import conflict between app.py and the app/ package.

Usage:
    gunicorn "wsgi:app"
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
