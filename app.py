import os, uuid
from flask import Flask, render_template, redirect, url_for, request, session, flash, abort
from msal import ConfidentialClientApplication
# Load database modules
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
# Load form modules
from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, StringField, EmailField, SubmitField, BooleanField, SelectMultipleField, FileField
from wtforms.validators import DataRequired, Email, Length, Regexp
# Load environment variables
from dotenv import load_dotenv
load_dotenv()
# Tools for RBAC
from functools import wraps
# Import config file
import config

### APP CONFIGURATION ###

# Define app and load configurations
app = Flask(__name__)
app.config.from_object(config.Config)

# Initialize SQLAlchemy and Migrate
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# MSAL client
app_instance = ConfidentialClientApplication(
    app.config['CLIENT_ID'],
    client_credential=app.config['CLIENT_SECRET'],
    authority=app.config['AUTHORITY']
)

# Check image extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

### MODELS ###
# Association table for users and roles
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True))

# Role model
class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __repr__(self):
        return f"<Role {self.name}>"

# User model
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    azure_id = db.Column(db.String(100), unique=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    roles = db.relationship('Role', secondary=user_roles, backref=db.backref('users', lazy='dynamic'))
    active = db.Column(db.Boolean(), default=True)

    requests = db.relationship('Request', back_populates='user', lazy=True)

    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)

    def __repr__(self):
        return f"<User {self.name}>"

# Requests model
class Request (db.Model):
    __tablename__ = 'requests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(10), nullable=False)
    req_type = db.Column(db.String(15), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    signature = db.Column(db.String(100), nullable=True)

    user = db.relationship('User', back_populates='requests')

# Decorator function to check roles
def role_required(role_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in', False):
                return redirect(url_for("login", next=request.url))

            # Get current user
            user = User.query.filter_by(azure_id=session['user']['sub']).first()

            if not user or not user.has_role(role_name):
                flash('You do not have permission to access this page', 'danger')
                return redirect(url_for("home"))

            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Create default roles
def create_default_roles():
    roles = {
        'admin': 'Full administrative access',
        'user': 'Standard user access',
        'manager': 'Academic manager access'
    }

    for role_name, description in roles.items():
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name, description=description)
            db.session.add(role)

    db.session.commit()

### FORMS ###

# Profile Form
class ProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    submit = SubmitField('Save Changes')

# User management form
class UserForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    active = BooleanField('Active', default=True)
    roles = SelectMultipleField('Roles', coerce=int)
    submit = SubmitField('Save Changes')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate roles from database
        self.roles.choices = [(role.id, role.name) for role in Role.query.all()]

class FERPAForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=25)])
    campus = StringField('Campus', validators=[DataRequired(), Length(min=2, max=25)])
    
    # Authorized checkpoints AND optional 'other' field

    # Categories checkpoints AND optional 'other' field

    release_to = StringField('Release to', validators=[DataRequired(), Length(max=25)])
    purpose = StringField('Purpose', validators=[DataRequired(), Length(max=25)])

    additional_names = StringField('Additional Individuals', validators=[DataRequired(), Length(max=25)])

    # Individuals checkpoints AND optional 'other' field

    password = StringField('Password', validators=[DataRequired(), Length(min=5, max=16)])

    peoplesoft_id = StringField('PSID', validators=[DataRequired(), Length(min=6, max=6)])
    signature = FileField('Upload Signature', validators=[DataRequired()])
    date = DateField('Birthdate', format='%Y-%m-%d', validators=[DataRequired()])

    submit = SubmitField('Submit FERPA')


class InfoChangeForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=25)])
    peoplesoft_id = StringField('UH ID', validators=[DataRequired(), Length(min=6, max=6)])

    # Choice for name/SSN

    # Section A: Name Change
    first_name_old = StringField('Old Name', validators=[Length(max=25)])
    middle_name_old = StringField('Old Mid. Name', validators=[Length(max=25)])
    last_name_old = StringField('Old Last Name', validators=[Length(max=25)])
    suffix_old = StringField('Old Suffix', validators=[Length(max=10)])

    first_name_new = StringField('Old Name', validators=[Length(max=25)])
    middle_name_new = StringField('Old Mid. Name', validators=[Length(max=25)])
    last_name_new = StringField('Old Last Name', validators=[Length(max=25)])
    suffix_new = StringField('Old Suffix', validators=[Length(max=10)])

    # Reason for name change checkbox

    # Section B: SSN Change
    ssn_old = StringField('Old SSN', validators=[Regexp(r"^\d{3}-\d{2}-\d{4}$", message="SSN must be in the format XXX-XX-XXXX")])
    ssn_new = StringField('New SSN', validators=[Regexp(r"^\d{3}-\d{2}-\d{4}$", message="SSN must be in the format XXX-XX-XXXX")])

    # Reason for SSN change checkbox

    # Signature and date
    signature = FileField('Upload Signature', validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])

    submit = SubmitField('Submit SSN/Name Change')

### ROUTES ###

# Display name of user if logged in or redirects to /login
@app.route('/')
@app.route('/home')
def home():
    # Check if user is logged in
    logged_in = session.get('logged_in', False)

    if logged_in:
        user = User.query.filter_by(azure_id=session['user']['sub']).first()
        is_admin = any(role.name == 'admin' for role in user.roles)
        return render_template('index.html', logged_in=logged_in, user=session['user'], is_admin=is_admin)

    return render_template('index.html', logged_in=logged_in)

## MICROSOFT ENTRA AUTHENTICATION ##
@app.route('/login')
def login():
    auth_url = app_instance.get_authorization_request_url(app.config['SCOPE'], redirect_uri=app.config['REDIRECT_URI'])
    return redirect(auth_url)

@app.route('/get_token')
def get_token():
    if "code" in request.args:
        # Get token from code
        result = app_instance.acquire_token_by_authorization_code(
            request.args['code'], app.config['SCOPE'], redirect_uri=app.config['REDIRECT_URI']
        )
        if "access_token" in result:
            # Get user info
            user_claims = result.get("id_token_claims")

            # Check if user exists in database
            existing_user = User.query.filter_by(azure_id=user_claims['sub']).first()
            
            if existing_user:
                # Check if account is active
                if not existing_user.active:
                    flash('Your account has been deactivated. Please contact an administrator.', 'danger')
                    return redirect(url_for("home"))

                # Store user data in session
                session['user'] = user_claims
                session['logged_in'] = True

                return redirect(url_for("home"))
            else:
                # Create new user
                user = User(
                    azure_id=user_claims['sub'],
                    name=user_claims.get('name'),
                    email=user_claims.get('preferred_username')
                )

                # Commit new user to database
                db.session.add(user)
                db.session.commit()
                
                # Store user data in session and redirect user to home
                session['user'] = user_claims
                session['logged_in'] = True
                return redirect(url_for("home"))
    
    return "Login failed", 401

## USER-SIDE MANAGEMENT ##
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    # Ensure the user is logged in
    logged_in = session.get('logged_in', False)
    if not logged_in:
        return redirect(url_for("login"))
    
    # Get current user
    user = User.query.filter_by(azure_id=session['user']['sub']).first()
    is_admin = any(role.name == 'admin' for role in user.roles)
    
    # Ensure the user exists
    if not user:
        flash('User not found', 'error')
        return redirect(url_for("home"))

    # Create form, populate with user data
    form = ProfileForm()

    # Manually populate the form
    if request.method == 'GET':
        form.name.data = user.name
        form.email.data = user.email

    # Handle form submission
    if form.validate_on_submit():
        # Update user info from form data
        user.name = form.name.data
        user.email = form.email.data

        # Update databasem, send message to user
        try:
            db.session.commit()
            flash('Profile updated successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')

        return redirect(url_for("profile"))

    return render_template('profile.html', form=form, logged_in=logged_in, is_admin=is_admin)

## ADMINISTRATOR MANAGEMENT ##

# View all users
@app.route('/admin/users')
@role_required('admin')
def manage_users():
    users = User.query.all()
    return render_template('manage_users.html', users=users, logged_in=True, is_admin=True)

# Create new users
@app.route('/admin/users/create', methods=['GET', 'POST'])
@role_required('admin')
def create_user():

    form = UserForm()
    
    if form.validate_on_submit():

        # Create a new user
        new_user = User(
            name=form.name.data,
            email=form.email.data,
            active=form.active.data
            )

        # Assign roles
        for role_id in form.roles.data:
            role = Role.query.get(role_id)
            if role:
                new_user.roles.append(role)

        db.session.add(new_user)
        db.session.commit()
        
        flash('User created successfully', 'success')
        return redirect(url_for('manage_users'))
    
    return render_template('create_user.html', form=form, logged_in=True, roles = Role.query.all(), is_admin=True)

# Update existing users
@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    
    if form.validate_on_submit():
        user.name = form.name.data
        user.email = form.email.data
        user.active = form.active.data

        # Update roles
        user.roles = []
        for role_id in form.roles.data:
            role = Role.query.get(role_id)
            if role:
                user.roles.append(role)

        db.session.commit()
        flash('User updated successfully.', 'success')
        return redirect(url_for('manage_users'))

    return render_template('edit_user.html', form=form, user=user, logged_in=True, is_admin=True)

# Delete users
@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@role_required('admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('manage_users'))

# Deactivate users
@app.route('/admin/users/<int:user_id>/deactivate', methods=['POST'])
@role_required('admin')
def deactivate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.active = False
    db.session.commit()
    flash('User account deactivated.', 'success')
    return redirect(url_for('manage_users'))

# Activate users
@app.route('/admin/users/<int:user_id>/activate', methods=['POST'])
@role_required('admin')
def activate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.active = True
    db.session.commit()
    flash('User account activated.', 'success')
    return redirect(url_for('manage_users'))

## APPROVAL & ACADEMIC REQUESTS ##

# Manager dashboard for request management
@app.route('/manager/requests')
@role_required('manager')
def manage_requests():
    return "manage requests"

# User dashboard for seeing requests
@app.route('/user/requests/manage')
@role_required('user')
def user_requests():
    logged_in = session.get('logged_in', False)

    print(logged_in)

    return render_template('user_requests.html', logged_in=logged_in)

# FERPA form page
@app.route('/user/requests/ferpa', methods=['GET', 'POST'])
@role_required('user')
def ferpa_request():
    # User FERPA form
    form = FERPAForm()

    if form.validate_on_submit():
        
        # Ensure the user uploaded a signature
        if 'signature' not in request.files:
            flash('Signature was not uploaded.', 'danger')
            return render_template('ferpa.html', form=form, logged_in=True)

        file = request.files['signature']
        if file.filename == '':
            flash('No file selected for signature.', 'danger')
            return render_template('ferpa.html', form=form, logged_in=True)

        # Check the file is allowed
        if file and allowed_file(file.filename):
            
            # Generate a unique name for the image
            unique_filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()

            # Save file with new name
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)

            # Get user id from session
            user = User.query.filter_by(azure_id=session['user']['sub']).first()
            user_id = user.id

            # Call function to build form
            # Will replace signature path with path to pdf

            # Create the request
            new_request = Request(
                user_id=user_id,
                status="pending",
                req_type="ferpa",
                signature=unique_filename)

            # Commit request to database
            db.session.add(new_request)
            db.session.commit()

            return redirect(url_for('user_requests'))

    return render_template('ferpa.html', form=form, logged_in=True)

# SSN/Name change form page
@app.route('/user/requests/info_change', methods=['GET', 'POST'])
@role_required('user')
def info_change_request():

    # Name/SSN change form
    form = InfoChangeForm()

    print(form.errors)
    print(form.csrf_token.errors)

    if form.validate_on_submit():
        # Ensure the user uploaded a signature
        if 'signature' not in request.files:
            flash('Signature was not uploaded.', 'danger')
            return render_template('info_change.html', form=form, logged_in=True)

        file = request.files['signature']
        if file.filename == '':
            flash('No file selected for signature.', 'danger')
            return render_template('info_change.html', form=form, logged_in=True)

        # Check the file is allowed
        if file and allowed_file(file.filename):
            
            # Generate a unique name for the image
            unique_filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()

            # Save file with new name
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)

            # Get user id from session
            user = User.query.filter_by(azure_id=session['user']['sub']).first()
            user_id = user.id

            new_request = Request(
                user_id=user_id,
                status="pending",
                req_type="info_change",
                signature=unique_filename)

            # Commit request to database
            db.session.add(new_request)
            db.session.commit()
            
            return redirect(url_for('user_requests'))

    return render_template('info_change.html', form=form, logged_in=True)

## MISCELLANEOUS ##
@app.route('/about')
def about():
    logged_in = session.get('logged_in', False)
    if logged_in:
        user = User.query.filter_by(azure_id=session['user']['sub']).first()
        is_admin = any(role.name == 'admin' for role in user.roles)
        return render_template('about.html', logged_in=logged_in, user=session['user'], is_admin=is_admin)

    return render_template('about.html', logged_in=logged_in)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.errorhandler(404)
def page_not_found(error):
    
    logged_in = session.get('logged_in', False)

    return render_template('404.html', logged_in=logged_in)

### APP & DATABASE INITIALIZATION ###

with app.app_context():
    db.create_all()
    create_default_roles()

if __name__ == "__main__":
    app.run(debug=True)
