"""
WSGI entry point for Vercel deployment
"""
from main import app

# Vercel requires the Flask app to be named 'app'
if __name__ == "__main__":
    app.run()