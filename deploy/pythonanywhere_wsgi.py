"""WSGI entry point for PythonAnywhere.

Copy the contents of this file into the WSGI configuration file that PythonAnywhere creates for the web app
(Web tab -> "WSGI configuration file" link), and replace YOUR_USERNAME with your PythonAnywhere username.
"""
import sys

# Folder that contains the cloned repository (the folder with app/, notebooks/, README.md)
PROJECT_DIR = "/home/YOUR_USERNAME/nyc-housing-transport"
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# The Dash app's underlying Flask server is what PythonAnywhere serves
from app.app import server as application  # noqa: E402,F401
