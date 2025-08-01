import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Define SQLAlchemy base class
class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///scout_manager.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'warning'

# Create tables
with app.app_context():
    # Import models to ensure they're registered with SQLAlchemy
    from models import User, Table, TableField, Record, RecordValue
    
    db.create_all()
    
    # Check if default tables exist, if not create them
    from helpers import initialize_default_tables
    initialize_default_tables()
    
    # Check if super admin exists, if not create one
    from helpers import create_default_admin
    create_default_admin()

# Import user loader
from models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
