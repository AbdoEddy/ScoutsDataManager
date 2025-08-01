
from app import app
from routes import *  # Import all routes

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
