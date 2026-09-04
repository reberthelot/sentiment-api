from backend import app as backend_app
from frontend import app as ui_app

# Point the root app to your backend API
app = backend_app

# Mount the UI sub-application onto the /ui route
app.mount("/ui", ui_app)