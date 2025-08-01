from flask import render_template, redirect, url_for, flash, request, jsonify, abort, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from models import User, Table, TableField, Record, RecordValue, PrintTemplate, GenericText, TablePermission, ROLE_READONLY, ROLE_EDITOR, ROLE_ADMIN
from forms import LoginForm, RegisterForm, UserManagementForm, TableForm, TableFieldForm, ChangePasswordForm
from helpers import admin_required, editor_required, create_dynamic_form, save_record
import json
from datetime import datetime, date, timedelta
from sqlalchemy import func, cast, Date

# Updating record access logic to handle all_access permissions
@app.route('/')
@login_required
def index():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'danger')
            return redirect(url_for('login'))

        login_user(user)
        next_page = request.args.get('next')
        if not next_page or next_page.startswith('/'):
            next_page = url_for('dashboard')

        flash(f'Bienvenue, {user.username}!', 'success')
        return redirect(next_page)

    return render_template('login.html', title='Connexion', form=form)

@app.route('/register', methods=['GET', 'POST'])
@login_required
@admin_required
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=ROLE_READONLY
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash('Le compte a été créé avec succès.', 'success')
        return redirect(url_for('manage_users'))

    return render_template('register.html', title='Créer un nouveau compte', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('login'))

@app.route('/settings')
@login_required
def settings():
    password_form = ChangePasswordForm()
    return render_template('settings.html', title='Paramètres', password_form=password_form)

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Votre mot de passe a été mis à jour.', 'success')
            return redirect(url_for('settings'))
        else:
            flash('Mot de passe actuel incorrect.', 'danger')
    return redirect(url_for('settings'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get counts for each table
    tables = Table.query.all()
    table_stats = []

    for table in tables:
        record_count = Record.query.filter_by(table_id=table.id).count()
        table_stats.append({
            'name': table.display_name,
            'count': record_count
        })

    # Get records trend data (last 7 days)
    records_trend_data = []
    for i in range(7):
        date = datetime.now().date() - timedelta(days=i)
        count = Record.query.filter(func.date(Record.created_at) == date).count()
        records_trend_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    records_trend_data.reverse()

    # Get activity by day of week
    activity_by_day = []
    days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    for day_num, day in enumerate(days):
        count = Record.query.filter(func.extract('dow', Record.created_at) == (day_num + 1) % 7).count()
        activity_by_day.append({
            'day': day,
            'count': count
        })

    # Get recent records with permission check
    if current_user.is_editor():
        recent_records = db.session.query(
            Record, Table
        ).join(
            Table, Record.table_id == Table.id
        ).order_by(
            Record.created_at.desc()
        ).limit(5).all()
    else:
        # Get all user's permissions
        permissions = TablePermission.query.filter_by(user_id=current_user.id).all()

        # Build conditions for each permission
        from sqlalchemy import or_
        conditions = []
        for permission in permissions:
            record_values = RecordValue.query.filter_by(
                field_id=permission.field_id,
                text_value=permission.match_value
            ).with_entities(RecordValue.record_id)
            conditions.append(Record.id.in_(record_values))

        if conditions:
            recent_records = db.session.query(
                Record, Table
            ).join(
                Table, Record.table_id == Table.id
            ).filter(or_(*conditions)).order_by(
                Record.created_at.desc()
            ).limit(5).all()
        else:
            recent_records = []

    record_list = []
    for record, table in recent_records:
        record_list.append({
            'id': record.id,
            'table_name': table.display_name,
            'created_at': record.created_at.strftime('%Y-%m-%d %H:%M'),
            'table_id': table.id
        })

    # Get user activity stats
    user_count = User.query.count()
    admin_count = User.query.filter_by(role=ROLE_ADMIN).count()
    editor_count = User.query.filter_by(role=ROLE_EDITOR).count()
    readonly_count = User.query.filter_by(role=ROLE_READONLY).count()

    record_count = Record.query.count()

    # Get today and this week's record count
    today = datetime.now().date()
    record_today_count = Record.query.filter(func.date(Record.created_at) == today).count()

    # Calculate first day of the current week (Monday)
    today_weekday = today.weekday()  # Monday=0, Sunday=6
    first_day_of_week = today - timedelta(days=today_weekday)
    record_week_count = Record.query.filter(
        func.date(Record.created_at) >= first_day_of_week
    ).count()

    # Generate data for record trends (last 14 days)
    records_trend_data = []

    for i in range(13, -1, -1):
        date_to_check = today - timedelta(days=i)
        count = Record.query.filter(func.date(Record.created_at) == date_to_check).count()
        records_trend_data.append({
            'date': date_to_check.strftime('%Y-%m-%d'),
            'count': count
        })

    # Calculate activity by day of week
    weekday_mapping = {
        0: 'Lundi',
        1: 'Mardi',
        2: 'Mercredi',
        3: 'Jeudi',
        4: 'Vendredi',
        5: 'Samedi',
        6: 'Dimanche'
    }

    activity_by_day = db.session.query(
        func.extract('dow', Record.created_at).label('weekday'), 
        func.count().label('count')
    ).group_by('weekday').all()

    activity_data = []
    for weekday, count in activity_by_day:
        # SQLite returns 0-6 where 0 is Sunday, PostgreSQL returns 0-6 where 0 is Sunday
        # Adjusting to ensure 0=Sunday regardless of database
        day_num = int(weekday)
        if day_num == 0:  # Sunday in PostgreSQL
            day_name = 'Dimanche'
        else:
            day_name = weekday_mapping.get(day_num - 1, f'Jour {day_num}')

        activity_data.append({
            'day': day_name,
            'count': count
        })

    return render_template(
        'dashboard.html', 
        title='Tableau de bord',
        table_stats=table_stats,
        recent_records=record_list,
        user_count=user_count,
        admin_count=admin_count,
        editor_count=editor_count,
        readonly_count=readonly_count,
        record_count=record_count,
        record_today_count=record_today_count,
        record_week_count=record_week_count,
        records_trend_data=json.dumps(records_trend_data),
        activity_by_day=json.dumps(activity_data)
    )

@app.route('/tables')
@login_required
def tables():
    tables = Table.query.all()
    return render_template('view_table.html', title='Consulter les données', tables=tables)

@app.route('/tables/<int:table_id>/records/pdf')
@login_required
def export_table_pdf(table_id):
    table = Table.query.get_or_404(table_id)
    fields = TableField.query.filter_by(table_id=table_id).order_by(TableField.order).all()

    # Get records with permission check
    if current_user.is_editor():
        records = Record.query.filter_by(table_id=table_id).all()
    else:
        # Get user's permissions for this table
        permissions = TablePermission.query.filter_by(
            user_id=current_user.id,
            table_id=table_id
        ).all()

        if not permissions:
            records = []
        else:
            # Check if user has all access
            has_all_access = any(p.all_access for p in permissions)

            if has_all_access:
                records = Record.query.filter_by(table_id=table_id).all()
            else:
                # Build query for records matching any permission
                from sqlalchemy import or_
                conditions = []
                for permission in permissions:
                    if not permission.all_access and permission.field_id and permission.match_value:
                        record_values = RecordValue.query.filter_by(
                            field_id=permission.field_id,
                            text_value=permission.match_value
                        ).with_entities(RecordValue.record_id)
                        conditions.append(Record.id.in_(record_values))

                if conditions:
                    records = Record.query.filter(
                        Record.table_id == table_id,
                        or_(*conditions)
                    ).all()
                else:
                    records = []

    # Get template
    template = PrintTemplate.query.filter_by(is_default=True).first()
    if not template:
        template = PrintTemplate(
            name="Default",
            header_html='<h1>{{table.display_name}}</h1>',
            footer_html='<p>Document généré le {{date}}</p>',
            is_default=True
        )
        db.session.add(template)
        db.session.commit()

    # Get values for all records
    records_data = []
    for record in records:
        values = {}
        for field in fields:
            value = RecordValue.query.filter_by(record_id=record.id, field_id=field.id).first()
            if value:
                values[field.name] = value.get_value()
            else:
                values[field.name] = None
        records_data.append(values)

    # Generate HTML
    from datetime import datetime
    return render_template(
        'print_table.html',
        table=table,
        fields=fields,
        records=records_data,
        template=template,
        date=datetime.now().strftime('%d/%m/%Y')
    )

@app.route('/tables/<int:table_id>/records')
@login_required
def table_records(table_id):
    table = Table.query.get_or_404(table_id)

    # If user is admin or editor, show all records
    if current_user.is_editor():
        records = Record.query.filter_by(table_id=table_id).order_by(Record.created_at.desc()).all()
    else:
        # Get user's permissions for this table
        permissions = TablePermission.query.filter_by(
            user_id=current_user.id,
            table_id=table_id
        ).all()

        if not permissions:
            records = []
        else:
            # Check if user has all access
            has_all_access = any(p.all_access for p in permissions)

            if has_all_access:
                records = Record.query.filter_by(table_id=table_id).order_by(Record.created_at.desc()).all()
            else:
                # Build query for records matching any permission
                from sqlalchemy import or_
                conditions = []
                for permission in permissions:
                    if not permission.all_access and permission.field_id and permission.match_value:
                        record_values = RecordValue.query.filter_by(
                            field_id=permission.field_id,
                            text_value=permission.match_value
                        ).with_entities(RecordValue.record_id)
                        conditions.append(Record.id.in_(record_values))

                if conditions:
                    records = Record.query.filter(
                        Record.table_id == table_id,
                        or_(*conditions)
                    ).order_by(Record.created_at.desc()).all()
                else:
                    records = []

    fields = TableField.query.filter_by(table_id=table_id).order_by(TableField.order).all()

    records_data = []
    for record in records:
        record_data = {'id': record.id, 'created_at': record.created_at.strftime('%Y-%m-%d %H:%M')}

        for field in fields:
            value = RecordValue.query.filter_by(record_id=record.id, field_id=field.id).first()
            if value:
                record_data[field.name] = value.get_value()
            else:
                record_data[field.name] = None

        records_data.append(record_data)

    return render_template(
        'view_table.html', 
        title=f'Données - {table.display_name}',
        table=table,
        fields=fields,
        records=records_data,
        is_records_view=True
    )

@app.route('/tables/<int:table_id>/records/<int:record_id>/pdf')
@login_required
def print_record(table_id, record_id):
    table = Table.query.get_or_404(table_id)
    record = Record.query.get_or_404(record_id)
    fields = TableField.query.filter_by(table_id=table_id).order_by(TableField.order).all()

    values = {}
    for field in fields:
        value = RecordValue.query.filter_by(record_id=record.id, field_id=field.id).first()
        if value:
            values[field.name] = value.get_value()
        else:
            values[field.name] = None

    template = PrintTemplate.query.filter_by(is_default=True).first()
    if not template:
        template = PrintTemplate(
            name="Default",
            header_html='<h1>{{table.display_name}}</h1>',
            footer_html='<p>Document généré le {{date}}</p>',
            is_default=True
        )
        db.session.add(template)
        db.session.commit()

    return render_template(
        'print_record.html',
        table=table,
        record=record,
        fields=fields,
        values=values,
        template=template,
        date=datetime.now().strftime('%d/%m/%Y')
    )

@app.route('/tables/<int:table_id>/records/<int:record_id>')
@login_required
def view_record(table_id, record_id):
    table = Table.query.get_or_404(table_id)
    record = Record.query.get_or_404(record_id)

    if record.table_id != table_id:
        flash('Enregistrement non trouvé.', 'danger')
        return redirect(url_for('table_records', table_id=table_id))

    fields = TableField.query.filter_by(table_id=table_id).order_by(TableField.order).all()
    values = {}

    for field in fields:
        value = RecordValue.query.filter_by(record_id=record.id, field_id=field.id).first()
        if value:
            values[field.name] = value.get_value()
        else:
            values[field.name] = None

    return render_template(
        'edit_record.html',
        title=f'Voir l\'enregistrement - {table.display_name}',
        table=table,
        record=record,
        fields=fields,
        values=values,
        view_only=True
    )

@app.route('/add_record', methods=['GET', 'POST'])
@login_required
@editor_required
def add_record():
    if request.method == 'GET':
        table_id = request.args.get('table_id')
        if table_id:
            return redirect(url_for('add_table_record', table_id=table_id))

        tables = Table.query.all()
        return render_template('add_record.html', title='Ajouter un enregistrement', tables=tables)

    return redirect(url_for('add_record'))

@app.route('/tables/<int:table_id>/add', methods=['GET', 'POST'])
@login_required
@editor_required
def add_table_record(table_id):
    table = Table.query.get_or_404(table_id)
    fields = TableField.query.filter_by(table_id=table_id).order_by(TableField.order).all()

    if request.method == 'POST':
        # First check unique constraints
        for field in fields:
            value = request.form.get(f'field_{field.id}')
            if field.unique and value:
                # Check if value already exists
                existing_value = RecordValue.query.join(Record).filter(
                    Record.table_id == table_id,
                    RecordValue.field_id == field.id,
                    RecordValue.text_value == value
                ).first()

                if existing_value:
                    flash(f'La valeur "{value}" existe déjà pour le champ "{field.display_name}".', 'danger')
                    return redirect(url_for('add_table_record', table_id=table_id))

        record = Record(table_id=table_id, created_by=current_user.id)
        db.session.add(record)
        db.session.flush()  # Get the record ID

        # Process each field
        for field in fields:
            value = request.form.get(f'field_{field.id}')

            if field.required and (value is None or value.strip() == ''):
                flash(f'Le champ "{field.display_name}" est obligatoire.', 'danger')
                return redirect(url_for('add_table_record', table_id=table_id))

            record_value = RecordValue(record_id=record.id, field_id=field.id)
            record_value.set_value(value, field.field_type)
            db.session.add(record_value)

        db.session.commit()
        flash('Enregistrement ajouté avec succès.', 'success')
        return redirect(url_for('table_records', table_id=table_id))

    return render_template(
        'add_record.html',
        title=f'Ajouter un enregistrement - {table.display_name}',
        table=table,
        fields=fields
    )

@app.route('/tables/<int:table_id>/records/<int:record_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required  # Changed from editor_required to admin_required
def edit_record(table_id, record_id):
    table = Table.query.get_or_404(table_id)
    record = Record.query.get_or_404(record_id)

    if record.table_id != table_id:
        flash('Enregistrement non trouvé.', 'danger')
        return redirect(url_for('table_records', table_id=table_id))

    fields = TableField.query.filter_by(table_id=table_id).order_by(TableField.order).all()

    if request.method == 'POST':
        # Update record values
        for field in fields:
            value = request.form.get(f'field_{field.id}')

            if field.required and (value is None or value.strip() == ''):
                flash(f'Le champ "{field.display_name}" est obligatoire.', 'danger')
                return redirect(url_for('edit_record', table_id=table_id, record_id=record_id))

            record_value = RecordValue.query.filter_by(record_id=record_id, field_id=field.id).first()

            if not record_value:
                record_value = RecordValue(record_id=record_id, field_id=field.id)
                db.session.add(record_value)

            record_value.set_value(value, field.field_type)

        record.modified_at = datetime.utcnow()
        db.session.commit()

        flash('Enregistrement mis à jour avec succès.', 'success')
        return redirect(url_for('table_records', table_id=table_id))

    # Get current values
    values = {}
    for field in fields:
        value = RecordValue.query.filter_by(record_id=record_id, field_id=field.id).first()
        if value:
            values[field.name] = value.get_value()
        else:
            values[field.name] = None

    return render_template(
        'edit_record.html',
        title=f'Modifier l\'enregistrement - {table.display_name}',
        table=table,
        record=record,
        fields=fields,
        values=values,
        view_only=False
    )

@app.route('/tables/<int:table_id>/records/<int:record_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_record(table_id, record_id):
    record = Record.query.get_or_404(record_id)

    if record.table_id != table_id:
        flash('Enregistrement non trouvé.', 'danger')
        return redirect(url_for('table_records', table_id=table_id))

    db.session.delete(record)
    db.session.commit()

    flash('Enregistrement supprimé avec succès.', 'success')
    return redirect(url_for('table_records', table_id=table_id))

@app.route('/manage_users')
@login_required
@admin_required
def manage_users():
    users = User.query.order_by(User.username).all()
    form = UserManagementForm()

    return render_template(
        'manage_users.html',
        title='Gestion des utilisateurs',
        users=users,
        form=form
    )

@app.route('/manage_users/add', methods=['POST'])
@login_required
@admin_required
def add_user():
    form = UserManagementForm()

    if form.validate_on_submit():
        # Check if username or email already exists
        username_exists = User.query.filter_by(username=form.username.data).first()
        email_exists = User.query.filter_by(email=form.email.data).first()

        if username_exists:
            flash('Ce nom d\'utilisateur est déjà pris.', 'danger')
            return redirect(url_for('manage_users'))

        if email_exists:
            flash('Cet email est déjà associé à un compte.', 'danger')
            return redirect(url_for('manage_users'))

        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data
        )

        if form.password.data:
            user.set_password(form.password.data)
        else:
            # Set a default password
            user.set_password('changeme')

        db.session.add(user)
        db.session.commit()

        flash('Utilisateur ajouté avec succès.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')

    return redirect(url_for('manage_users'))

@app.route('/manage_users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    # Prevent editing the current admin
    if user.id == current_user.id:
        flash('Vous ne pouvez pas modifier votre propre compte ici.', 'warning')
        return redirect(url_for('manage_users'))

    if request.method == 'POST':
        form = UserManagementForm()

        if form.validate_on_submit():
            # Check for username and email conflicts
            username_user = User.query.filter_by(username=form.username.data).first()
            if username_user and username_user.id != user_id:
                flash('Ce nom d\'utilisateur est déjà pris.', 'danger')
                return redirect(url_for('edit_user', user_id=user_id))

            email_user = User.query.filter_by(email=form.email.data).first()
            if email_user and email_user.id != user_id:
                flash('Cet email est déjà associé à un compte.', 'danger')
                return redirect(url_for('edit_user', user_id=user_id))

            user.username = form.username.data
            user.email = form.email.data
            user.role = form.role.data

            if form.password.data:
                user.set_password(form.password.data)

            db.session.commit()
            flash('Utilisateur mis à jour avec succès.', 'success')
            return redirect(url_for('manage_users'))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{getattr(form, field).label.text}: {error}', 'danger')
            return redirect(url_for('edit_user', user_id=user_id))

    form = UserManagementForm(obj=user)
    form.password.data = ''  # Clear password field

    return render_template(
        'manage_users.html',
        title='Modifier l\'utilisateur',
        edit_user=user,
        form=form,
        users=User.query.order_by(User.username).all()
    )

@app.route('/manage_users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    # Prevent deleting the current admin
    if user.id == current_user.id:
        flash('Vous ne pouvez pas supprimer votre propre compte.', 'danger')
        return redirect(url_for('manage_users'))

    db.session.delete(user)
    db.session.commit()

    flash('Utilisateur supprimé avec succès.', 'success')
    return redirect(url_for('manage_users'))

@app.route('/manage_tables')
@login_required
@admin_required
def manage_tables():
    tables = Table.query.all()
    form = TableForm()

    return render_template(
        'manage_table.html',
        title='Gestion des tables',
        tables=tables,
        form=form,
        manage_mode='tables'
    )

@app.route('/manage_tables/add', methods=['POST'])
@login_required
@admin_required
def add_table():
    form = TableForm()

    if form.validate_on_submit():
        # Check if table name already exists
        existing_table = Table.query.filter_by(name=form.name.data).first()

        if existing_table:
            flash('Une table avec ce nom existe déjà.', 'danger')
            return redirect(url_for('manage_tables'))

        table = Table(
            name=form.name.data,
            display_name=form.display_name.data,
            description=form.description.data
        )

        db.session.add(table)
        db.session.commit()

        flash('Table ajoutée avec succès.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')

    return redirect(url_for('manage_tables'))

@app.route('/manage_tables/<int:table_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_table(table_id):
    table = Table.query.get_or_404(table_id)

    if request.method == 'POST':
        form = TableForm()

        if form.validate_on_submit():
            # Check for name conflicts
            name_table = Table.query.filter_by(name=form.name.data).first()
            if name_table and name_table.id != table_id:
                flash('Une table avec ce nom existe déjà.', 'danger')
                return redirect(url_for('edit_table', table_id=table_id))

            table.name = form.name.data
            table.display_name = form.display_name.data
            table.description = form.description.data

            db.session.commit()
            flash('Table mise à jour avec succès.', 'success')
            return redirect(url_for('manage_tables'))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{getattr(form, field).label.text}: {error}', 'danger')
            return redirect(url_for('edit_table', table_id=table_id))

    form = TableForm(obj=table)

    return render_template(
        'manage_table.html',
        title='Modifier la table',
        edit_table=table,
        form=form,
        tables=Table.query.all(),
        manage_mode='tables'
    )

@app.route('/manage_tables/<int:table_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_table(table_id):
    table = Table.query.get_or_404(table_id)

    db.session.delete(table)
    db.session.commit()

    flash('Table supprimée avec succès.', 'success')
    return redirect(url_for('manage_tables'))

@app.route('/manage_tables/<int:table_id>/fields')
@login_required
@admin_required
def manage_fields(table_id):
    table = Table.query.get_or_404(table_id)
    fields = TableField.query.filter_by(table_id=table_id).order_by(TableField.order).all()
    form = TableFieldForm()

    return render_template(
        'manage_table.html',
        title=f'Gestion des champs - {table.display_name}',
        table=table,
        fields=fields,
        form=form,
        manage_mode='fields'
    )

@app.route('/manage_tables/<int:table_id>/fields/add', methods=['POST'])
@login_required
@admin_required
def add_field(table_id):
    table = Table.query.get_or_404(table_id)
    form = TableFieldForm()

    if form.validate_on_submit():
        # Check if field name already exists for thistable
        existing_field = TableField.query.filter_by(table_id=table_id, name=form.name.data).first()

        if existing_field:
            flash('Un champ avec ce nom existe déjà dans cette table.', 'danger')
            return redirect(url_for('manage_fields', table_id=table_id))

        # Get the next order value
        max_order = db.session.query(func.max(TableField.order)).filter_by(table_id=table_id).scalar()
        next_order = 1 if max_order is None else max_order + 1

        field = TableField(
            table_id=table_id,
            name=form.name.data,
            display_name=form.display_name.data,
            field_type=form.field_type.data,
            required=form.required.data,
            order=next_order
        )

        # Process options for dropdown
        if form.field_type.data == 'dropdown' and form.options.data:
            options_list = [option.strip() for option in form.options.data.split('\n') if option.strip()]
            field.set_options(options_list)

        db.session.add(field)
        db.session.commit()

        flash('Champ ajouté avec succès.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')

    return redirect(url_for('manage_fields', table_id=table_id))

@app.route('/manage_tables/<int:table_id>/fields/<int:field_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_field(table_id, field_id):
    table = Table.query.get_or_404(table_id)
    field = TableField.query.get_or_404(field_id)

    if field.table_id != table_id:
        flash('Champ non trouvé.', 'danger')
        return redirect(url_for('manage_fields', table_id=table_id))

    if request.method == 'POST':
        form = TableFieldForm()

        if form.validate_on_submit():
            # Check for name conflicts
            name_field = TableField.query.filter_by(table_id=table_id, name=form.name.data).first()
            if name_field and name_field.id != field_id:
                flash('Un champ avec ce nom existe déjà dans cette table.', 'danger')
                return redirect(url_for('edit_field', table_id=table_id, field_id=field_id))

            field.name = form.name.data
            field.display_name = form.display_name.data
            field.field_type = form.field_type.data
            field.required = form.required.data
            field.unique = form.unique.data

            # Process options for dropdown
            if form.field_type.data == 'dropdown' and form.options.data:
                options_list = [option.strip() for option in form.options.data.split('\n') if option.strip()]
                field.set_options(options_list)
            else:
                field.options = None

            db.session.commit()
            flash('Champ mis à jour avec succès.', 'success')
            return redirect(url_for('manage_fields', table_id=table_id))
        else:
            for field_name, errors in form.errors.items():
                for error in errors:
                    flash(f'{getattr(form, field_name).label.text}: {error}', 'danger')
            return redirect(url_for('edit_field', table_id=table_id, field_id=field_id))

    form = TableFieldForm(obj=field)

    # Set options for dropdown
    if field.field_type == 'dropdown' and field.options:
        options_list = field.get_options()
        form.options.data = '\n'.join(options_list)

    return render_template(
        'manage_table.html',
        title=f'Modifier le champ - {field.display_name}',
        table=table,
        edit_field=field,
        form=form,
        fields=TableField.query.filter_by(table_id=table_id).order_by(TableField.order).all(),
        manage_mode='fields'
    )

@app.route('/manage_tables/<int:table_id>/fields/<int:field_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_field(table_id, field_id):
    field = TableField.query.get_or_404(field_id)

    if field.table_id != table_id:
        flash('Champ non trouvé.', 'danger')
        return redirect(url_for('manage_fields', table_id=table_id))

    db.session.delete(field)
    db.session.commit()

    flash('Champ supprimé avec succès.', 'success')
    return redirect(url_for('manage_fields', table_id=table_id))

@app.route('/manage_tables/<int:table_id>/fields/order', methods=['POST'])
@login_required
@admin_required
def reorder_fields(table_id):
    data = request.get_json()

    if not data or 'fields' not in data:
        return jsonify({'success': False, 'message': 'Données invalides'}), 400

    field_orders = data['fields']

    for field_id, order in field_orders.items():
        field = TableField.query.get(int(field_id))

        if field and field.table_id == table_id:
            field.order = order

    db.session.commit()

    return jsonify({'success': True})
@app.route('/manage_print_templates')
@login_required
@admin_required
def manage_print_templates():
    templates = PrintTemplate.query.all()
    return render_template('manage_print_templates.html', templates=templates)

@app.route('/print/generic_text/autorisation_camp')
@login_required
def print_generic_text():
    text = GenericText.query.filter_by(name='autorisation_camp').first()
    if not text:
        text = GenericText(
            name='autorisation_camp',
            content='<h2>Autorisation de Camp</h2><p>Je soussigné(e), [nom du parent], autorise [nom de l\'enfant] à participer au camp scout qui se déroulera du [date début] au [date fin] à [lieu].</p><p>Fait à _________________, le _________________</p><p>Signature: _________________</p>'
        )
        db.session.add(text)
        db.session.commit()

    template = PrintTemplate.query.filter_by(is_default=True).first()
    if not template:
        template = PrintTemplate(
            name="Default",
            header_html='<h1>Gestion des Scouts</h1>',
            footer_html='<p>Document généré le {{date}}</p>',
            is_default=True
        )
        db.session.add(template)
        db.session.commit()

    return render_template(
        'print_generic_text.html',
        text=text,
        template=template,
        date=datetime.now().strftime('%d/%m/%Y')
    )

@app.route('/api/print_template/active')
def get_active_template():
    template = PrintTemplate.query.filter_by(is_default=True).first()
    if not template:
        template = PrintTemplate(
            name="Default",
            header_html='<h1>Gestion des Scouts</h1>',
            footer_html='<p>Document généré le ${new Date().toLocaleDateString("fr-FR")}</p>',
            is_default=True
        )
        db.session.add(template)
        db.session.commit()
    return jsonify({
        'header_html': template.header_html,
        'footer_html': template.footer_html,
        'css': template.css,
        'logo_url': template.logo_url
    })

@app.route('/manage_print_templates/<int:template_id>', methods=['POST'])
@login_required
@admin_required
def update_print_template(template_id):
    template = PrintTemplate.query.get_or_404(template_id)
    template.header_html = request.form.get('header_html', '')
    template.footer_html = request.form.get('footer_html', '')
    template.css = request.form.get('css', '')
    template.logo_url = request.form.get('logo_url', '')
    db.session.commit()
    flash('Template updated successfully', 'success')
    return redirect(url_for('manage_print_templates'))

@app.route('/manage_table_permissions', methods=['GET', 'POST'])
@app.route('/manage_table_permissions/<int:table_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_table_permissions(table_id=None):
    tables = Table.query.all()
    users = User.query.all()

    if table_id is None and tables:
        table_id = tables[0].id

    current_table = Table.query.get_or_404(table_id) if table_id else None
    fields = TableField.query.filter_by(table_id=table_id).all() if table_id else []
    permissions = TablePermission.query.filter_by(table_id=table_id).all() if table_id else []

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        permission_type = request.form.get('permission_type')
        field_id = request.form.get('field_id')
        match_value = request.form.get('match_value')

        if user_id and permission_type:
            if permission_type == 'all_access':
                # Remove existing permissions for this user and table
                TablePermission.query.filter_by(user_id=user_id, table_id=table_id).delete()
                
                permission = TablePermission(
                    user_id=user_id,
                    table_id=table_id,
                    field_id=None,
                    match_value=None,
                    all_access=True
                )
                db.session.add(permission)
                db.session.commit()
                flash('Permission d\'accès total ajoutée avec succès.', 'success')
            elif permission_type == 'specific' and field_id and match_value:
                permission = TablePermission(
                    user_id=user_id,
                    table_id=table_id,
                    field_id=field_id,
                    match_value=match_value,
                    all_access=False
                )
                db.session.add(permission)
                db.session.commit()
                flash('Permission spécifique ajoutée avec succès.', 'success')
            else:
                flash('Veuillez remplir tous les champs requis.', 'danger')
            
            return redirect(url_for('manage_table_permissions', table_id=table_id))

    return render_template(
        'manage_table_permissions.html',
        tables=tables,
        current_table=current_table,
        users=users,
        fields=fields,
        permissions=permissions
    )

@app.route('/manage_table_permissions/<int:table_id>/delete/<int:permission_id>', methods=['POST'])
@login_required
@admin_required
def delete_table_permission(table_id, permission_id):
    permission = TablePermission.query.get_or_404(permission_id)
    if permission.table_id != table_id:
        abort(404)

    db.session.delete(permission)
    db.session.commit()
    flash('Permission removed successfully.', 'success')
    return redirect(url_for('manage_table_permissions', table_id=table_id))

@app.route('/manage_table_permissions/<int:table_id>/bulk_grant', methods=['POST'])
@login_required
@admin_required
def bulk_grant_permissions(table_id):
    user_id = request.form.get('user_id')

    if not user_id:
        flash('Please select a user.', 'danger')
        return redirect(url_for('manage_table_permissions', table_id=table_id))

    table = Table.query.get_or_404(table_id)
    user = User.query.get_or_404(user_id)

    # Remove existing permissions for this user and table
    TablePermission.query.filter_by(user_id=user_id, table_id=table_id).delete()

    # Create a single all_access permission
    permission = TablePermission(
        user_id=user_id,
        table_id=table_id,
        field_id=None,
        match_value=None,
        all_access=True
    )
    db.session.add(permission)
    db.session.commit()
    
    flash(f'Granted full access to all data for {user.username}.', 'success')
    return redirect(url_for('manage_table_permissions', table_id=table_id))

@app.route('/manage_generic_text/<name>', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_generic_text(name):
    text = GenericText.query.filter_by(name=name).first()
    if not text:
        text = GenericText(
            name=name,
            content='Texte par défaut'
        )
        db.session.add(text)
        db.session.commit()

    if request.method == 'POST':
        text.content = request.form.get('content', '')
        db.session.commit()
        flash('Texte mis à jour avec succès.', 'success')
        return redirect(url_for('manage_generic_text', name=name))

    return render_template('manage_generic_text.html', text=text)
    template.header_html = request.form.get('header_html', '')
    template.footer_html = request.form.get('footer_html', '')
    template.css = request.form.get('css', '')
    template.logo_url = request.form.get('logo_url', '')
    db.session.commit()
    return redirect(url_for('manage_print_templates'))
@app.route('/tables/<int:table_id>/export', methods=['GET', 'POST'])
@login_required
def export_table(table_id):
    table = Table.query.get_or_404(table_id)
    fields = TableField.query.filter_by(table_id=table_id).order_by(TableField.order).all()

    if request.method == 'POST':
        selected_fields = request.form.getlist('fields')

        # Get records with permission check
        if current_user.is_editor():
            records_query = Record.query.filter_by(table_id=table_id)
        else:
            # Get user's permissions for this table
            permissions = TablePermission.query.filter_by(
                user_id=current_user.id,
                table_id=table_id
            ).all()

            if not permissions:
                records_query = Record.query.filter_by(id=0)  # Return empty set
            else:
                # Check if user has all access
                has_all_access = any(p.all_access for p in permissions)

                if has_all_access:
                    records_query = Record.query.filter_by(table_id=table_id)
                else:
                    # Build query for records matching any permission
                    from sqlalchemy import or_
                    conditions = []
                    for permission in permissions:
                        record_values = RecordValue.query.filter_by(
                            field_id=permission.field_id
                        ).filter(
                            RecordValue.text_value == permission.match_value
                        ).with_entities(RecordValue.record_id)
                        conditions.append(Record.id.in_(record_values))

                    records_query = Record.query.filter(
                        Record.table_id == table_id,
                        or_(*conditions)
                    )

        # Apply additional filters
        for field in fields:
            filter_value = request.form.get(f'filter_{field.id}')
            if filter_value:
                # Get record IDs that match the filter
                matching_records = RecordValue.query.filter_by(
                    field_id=field.id
                ).filter(
                    RecordValue.text_value == filter_value
                ).with_entities(RecordValue.record_id)
                records_query = records_query.filter(Record.id.in_(matching_records))

        records = records_query.all()

        import pandas as pd
        from io import BytesIO

        data = []
        for record in records:
            row = {}
            for field_id in selected_fields:
                field = TableField.query.get(field_id)
                value = RecordValue.query.filter_by(record_id=record.id, field_id=field.id).first()
                row[field.display_name] = value.get_value() if value else None
            data.append(row)

        df = pd.DataFrame(data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Data', index=False)

        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'{table.name}_export.xlsx'
        )

    return render_template('export_table.html', table=table, fields=fields)