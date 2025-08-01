from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

# Define roles as constants
ROLE_READONLY = 'readonly'
ROLE_EDITOR = 'editor'
ROLE_ADMIN = 'admin'

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_READONLY)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == ROLE_ADMIN

    def is_editor(self):
        return self.role == ROLE_EDITOR or self.role == ROLE_ADMIN

    def __repr__(self):
        return f'<User {self.username}>'

class Table(db.Model):
    __tablename__ = 'tables'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    fields = db.relationship('TableField', backref='table', cascade='all, delete-orphan')
    records = db.relationship('Record', backref='table', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Table {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'fields': [field.to_dict() for field in self.fields]
        }

class TableField(db.Model):
    __tablename__ = 'table_fields'

    id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey('tables.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    field_type = db.Column(db.String(50), nullable=False)  # text, number, date, dropdown, etc.
    required = db.Column(db.Boolean, default=False)
    unique = db.Column(db.Boolean, default=False)  # New unique constraint field
    options = db.Column(db.Text, nullable=True)  # JSON string for dropdown options
    order = db.Column(db.Integer, default=0)

    # Relationships
    values = db.relationship('RecordValue', backref='field', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<TableField {self.name} ({self.field_type})>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'field_type': self.field_type,
            'required': self.required,
            'unique': self.unique,
            'options': json.loads(self.options) if self.options else [],
            'order': self.order
        }

    def get_options(self):
        if not self.options:
            return []
        return json.loads(self.options)

    def set_options(self, options_list):
        self.options = json.dumps(options_list)

class Record(db.Model):
    __tablename__ = 'records'

    id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey('tables.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    values = db.relationship('RecordValue', backref='record', cascade='all, delete-orphan')
    creator = db.relationship('User', backref='created_records')

    def __repr__(self):
        return f'<Record {self.id} for Table {self.table_id}>'

    def to_dict(self):
        values_dict = {}
        for value in self.values:
            values_dict[value.field.name] = value.get_value()

        return {
            'id': self.id,
            'table_id': self.table_id,
            'created_by': self.created_by,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'modified_at': self.modified_at.strftime('%Y-%m-%d %H:%M'),
            'values': values_dict,
            'creator': self.creator.username
        }

class RecordValue(db.Model):
    __tablename__ = 'record_values'

    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('records.id'), nullable=False)
    field_id = db.Column(db.Integer, db.ForeignKey('table_fields.id'), nullable=False)
    text_value = db.Column(db.Text, nullable=True)
    number_value = db.Column(db.Float, nullable=True)
    date_value = db.Column(db.Date, nullable=True)

    def __repr__(self):
        return f'<RecordValue for Record {self.record_id}, Field {self.field_id}>'

    def set_value(self, value, field_type):
        if field_type == 'text' or field_type == 'dropdown':
            self.text_value = value
        elif field_type == 'number':
            self.number_value = float(value) if value else None
        elif field_type == 'date':
            if isinstance(value, str) and value:
                self.date_value = datetime.strptime(value, '%Y-%m-%d').date()
            else:
                self.date_value = value

    def get_value(self):
        if self.field.field_type == 'text' or self.field.field_type == 'dropdown':
            return self.text_value
        elif self.field.field_type == 'number':
            return self.number_value
        elif self.field.field_type == 'date':
            return self.date_value.strftime('%Y-%m-%d') if self.date_value else None
        return None
class PrintTemplate(db.Model):
    __tablename__ = 'print_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    header_html = db.Column(db.Text)
    footer_html = db.Column(db.Text)
    css = db.Column(db.Text)
    logo_url = db.Column(db.String(255))
    is_default = db.Column(db.Boolean, default=False)

class ReportTemplate(db.Model):
    __tablename__ = 'report_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    template_html = db.Column(db.Text, nullable=False)
    fields = db.Column(db.Text)  # JSON list of field IDs
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TablePermission(db.Model):
    __tablename__ = 'table_permissions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    table_id = db.Column(db.Integer, db.ForeignKey('tables.id'), nullable=False)
    field_id = db.Column(db.Integer, db.ForeignKey('table_fields.id'), nullable=True)
    match_value = db.Column(db.String(255), nullable=True)
    all_access = db.Column(db.Boolean, default=False)  # New field for bulk access
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='table_permissions')
    table = db.relationship('Table', backref='permissions')
    field = db.relationship('TableField', backref='permissions')

class GenericText(db.Model):
    __tablename__ = 'generic_texts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)