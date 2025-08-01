from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
from app import db
from models import User, Table, TableField, ROLE_ADMIN, ROLE_READONLY, ROLE_EDITOR
import json

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('Vous n\'avez pas la permission d\'accéder à cette page.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def editor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_editor():
            flash('Vous n\'avez pas la permission d\'accéder à cette page.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def create_dynamic_form(fields, values=None):
    """
    Create a dynamic form based on field definitions
    
    Args:
        fields (list): List of TableField objects
        values (dict, optional): Dictionary of values to populate the form
        
    Returns:
        dict: Dictionary containing form field information
    """
    form_fields = []
    
    for field in fields:
        field_info = {
            'id': field.id,
            'name': field.name,
            'display_name': field.display_name,
            'type': field.field_type,
            'required': field.required
        }
        
        if field.field_type == 'dropdown' and field.options:
            field_info['options'] = field.get_options()
        
        if values and field.name in values:
            field_info['value'] = values[field.name]
        
        form_fields.append(field_info)
    
    return form_fields

def save_record(table_id, form_data, record_id=None, created_by=None):
    """
    Save a record to the database
    
    Args:
        table_id (int): ID of the table
        form_data (dict): Form data
        record_id (int, optional): ID of the record to update
        created_by (int, optional): ID of the user who created the record
        
    Returns:
        bool: True if successful, False otherwise
    """
    from models import Record, RecordValue
    
    try:
        if record_id:
            # Update existing record
            record = Record.query.get(record_id)
            if not record or record.table_id != table_id:
                return False
        else:
            # Create new record
            record = Record(table_id=table_id, created_by=created_by)
            db.session.add(record)
            db.session.flush()
        
        fields = TableField.query.filter_by(table_id=table_id).all()
        
        for field in fields:
            field_key = f'field_{field.id}'
            
            if field_key not in form_data:
                continue
                
            value = form_data[field_key]
            
            # Check if value already exists
            record_value = RecordValue.query.filter_by(record_id=record.id, field_id=field.id).first()
            
            if not record_value:
                record_value = RecordValue(record_id=record.id, field_id=field.id)
                db.session.add(record_value)
            
            record_value.set_value(value, field.field_type)
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error saving record: {str(e)}")
        return False

def initialize_default_tables():
    """Initialize the default tables if they don't exist"""
    default_tables = [
        {
            'name': 'autorisation_camp',
            'display_name': 'Autorisation de Camp',
            'fields': [
                {'name': 'nom_camp', 'display_name': 'Nom du camp', 'type': 'text', 'required': True},
                {'name': 'date_debut', 'display_name': 'Date de début', 'type': 'date', 'required': True},
                {'name': 'date_fin', 'display_name': 'Date de fin', 'type': 'date', 'required': True},
                {'name': 'lieu', 'display_name': 'Lieu', 'type': 'text', 'required': True},
                {'name': 'responsable', 'display_name': 'Responsable', 'type': 'text', 'required': True}
            ]
        },
        {
            'name': 'accident',
            'display_name': 'Accident',
            'fields': [
                {'name': 'date', 'display_name': 'Date', 'type': 'date', 'required': True},
                {'name': 'lieu', 'display_name': 'Lieu', 'type': 'text', 'required': True},
                {'name': 'scout_affecte', 'display_name': 'Scout affecté', 'type': 'text', 'required': True},
                {'name': 'description', 'display_name': 'Description', 'type': 'text', 'required': True},
                {'name': 'mesures_prises', 'display_name': 'Mesures prises', 'type': 'text', 'required': True}
            ]
        },
        {
            'name': 'cotisation',
            'display_name': 'Cotisation',
            'fields': [
                {'name': 'scout', 'display_name': 'Scout', 'type': 'text', 'required': True},
                {'name': 'montant', 'display_name': 'Montant', 'type': 'number', 'required': True},
                {'name': 'date_paiement', 'display_name': 'Date de paiement', 'type': 'date', 'required': True},
                {'name': 'methode_paiement', 'display_name': 'Méthode de paiement', 'type': 'dropdown', 'required': True, 
                 'options': ['Espèces', 'Chèque', 'Virement bancaire', 'Autre']}
            ]
        },
        {
            'name': 'activites',
            'display_name': 'Activités',
            'fields': [
                {'name': 'nom', 'display_name': 'Nom', 'type': 'text', 'required': True},
                {'name': 'date', 'display_name': 'Date', 'type': 'date', 'required': True},
                {'name': 'lieu', 'display_name': 'Lieu', 'type': 'text', 'required': True},
                {'name': 'type', 'display_name': 'Type', 'type': 'dropdown', 'required': True,
                 'options': ['Réunion', 'Sortie', 'Camp', 'Formation', 'Autre']},
                {'name': 'nombre_participants', 'display_name': 'Nombre de participants', 'type': 'number', 'required': True}
            ]
        }
    ]
    
    # Check if tables exist
    for table_data in default_tables:
        table = Table.query.filter_by(name=table_data['name']).first()
        
        if not table:
            # Create the table
            table = Table(
                name=table_data['name'],
                display_name=table_data['display_name']
            )
            db.session.add(table)
            db.session.flush()
            
            # Create the fields
            for i, field_data in enumerate(table_data['fields']):
                field = TableField(
                    table_id=table.id,
                    name=field_data['name'],
                    display_name=field_data['display_name'],
                    field_type=field_data['type'],
                    required=field_data['required'],
                    order=i + 1
                )
                
                if 'options' in field_data and field_data['type'] == 'dropdown':
                    field.set_options(field_data['options'])
                
                db.session.add(field)
    
    db.session.commit()

def create_default_admin():
    """Create a default admin user if no users exist"""
    user_count = User.query.count()
    
    if user_count == 0:
        admin = User(
            username='admin',
            email='admin@example.com',
            role=ROLE_ADMIN
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        db.session.commit()
