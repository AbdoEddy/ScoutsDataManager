from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SelectField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
from models import User, ROLE_READONLY, ROLE_EDITOR, ROLE_ADMIN

class LoginForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    submit = SubmitField('Se connecter')

class RegisterForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=3, max=64)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirmer le mot de passe', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('S\'inscrire')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Ce nom d\'utilisateur est déjà pris. Veuillez en choisir un autre.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Cet email est déjà associé à un compte.')

def validate_password_complexity(form, field):
    password = field.data
    if len(password) < 8:
        raise ValidationError('Le mot de passe doit contenir au moins 8 caractères.')
    if not any(c.isupper() for c in password):
        raise ValidationError('Le mot de passe doit contenir au moins une majuscule.')
    if not any(c.islower() for c in password):
        raise ValidationError('Le mot de passe doit contenir au moins une minuscule.')
    if not any(c.isdigit() for c in password):
        raise ValidationError('Le mot de passe doit contenir au moins un chiffre.')
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        raise ValidationError('Le mot de passe doit contenir au moins un caractère spécial.')

class UserManagementForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=3, max=64)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Rôle', choices=[
        (ROLE_READONLY, 'Lecture seule'),
        (ROLE_EDITOR, 'Éditeur'),
        (ROLE_ADMIN, 'Administrateur')
    ], validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[
        Optional(),
        validate_password_complexity
    ])
    password2 = PasswordField('Confirmer le mot de passe', validators=[EqualTo('password')])
    submit = SubmitField('Enregistrer')

class TableForm(FlaskForm):
    name = StringField('Nom technique', validators=[DataRequired(), Length(max=100)])
    display_name = StringField('Nom d\'affichage', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    submit = SubmitField('Enregistrer')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Mot de passe actuel', validators=[DataRequired()])
    new_password = PasswordField('Nouveau mot de passe', validators=[
        DataRequired(),
        validate_password_complexity
    ])
    confirm_password = PasswordField('Confirmer le nouveau mot de passe', validators=[
        DataRequired(),
        EqualTo('new_password')
    ])
    submit = SubmitField('Changer le mot de passe')

class TableFieldForm(FlaskForm):
    name = StringField('Nom technique', validators=[DataRequired(), Length(max=100)])
    display_name = StringField('Nom d\'affichage', validators=[DataRequired(), Length(max=100)])
    field_type = SelectField('Type de champ', choices=[
        ('text', 'Texte'),
        ('number', 'Nombre'),
        ('date', 'Date'),
        ('dropdown', 'Liste déroulante')
    ], validators=[DataRequired()])
    required = BooleanField('Obligatoire')
    unique = BooleanField('Valeur unique')
    options = TextAreaField('Options (une par ligne, pour les listes déroulantes)')
    submit = SubmitField('Enregistrer')