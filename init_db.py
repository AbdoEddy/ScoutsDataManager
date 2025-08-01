"""
Database initialization script for Scout Management application.
Run this script to create the database tables and set up the initial admin user.
"""

import os
from app import app, db
from models import User, Table, TableField, Record, RecordValue, PrintTemplate, GenericText, ROLE_ADMIN

def init_db():
    with app.app_context():
        db.create_all()

        # Create admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@example.com',
                role=ROLE_ADMIN
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")