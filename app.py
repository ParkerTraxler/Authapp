import os, uuid
from flask import Flask, render_template, redirect, url_for, request, flash, session
from msal import ConfidentialClientApplication
# Load database modules
from models import db, User, Role, Request
from flask_migrate import Migrate
# Forms
from forms import ProfileForm, UserForm, FERPAForm, InfoChangeForm
# Environment Variables
from dotenv import load_dotenv
load_dotenv()
# Tools for RBAC
from decorators import role_required
# Import config file
import config

### APP CONFIGURATION ###

# Define app and load configurations
app = Flask(__name__)
app.config.from_object(config.Config)

# Initialize SQLAlchemy and Migrate
db.init_app(app)
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
@app.route('/manager/requests/manage')
@role_required('manager')
def manage_requests():
    pending_requests = Request.query.filter_by(status='pending').all()
    returned_requests = Request.query.filter_by(status='returned').all()
    approved_requests = Request.query.filter_by(status='approved').all()
    return render_template('manage_requests.html', 
                           pending_requests=pending_requests, 
                           returned_requests=returned_requests,
                           approved_requests=approved_requests,
                           logged_in=True)

@app.route('/manager/requests/approve/<int:request_id>', methods=['POST'])
@role_required('manager')
def approve_request(request_id):
    req = Request.query.get_or_404(request_id)
    req.status = 'approved'
    
    db.session.commit()
    
    flash('Request approved successfully.', 'success')
    return redirect(url_for('manage_requests'))

@app.route('/manager/requests/return/<int:request_id>', methods=['POST'])
@role_required('manager')
def return_request(request_id):
    req = Request.query.get_or_404(request_id)
    req.status = 'returned'
    
    db.session.commit()
    
    flash('Request returned successfully.', 'warning')
    return redirect(url_for('manage_requests'))

# User dashboard for seeing requests
@app.route('/user/requests/manage')
@role_required('user')
def user_requests():
   
    # Get user id for requests
    user = User.query.filter_by(azure_id=session['user']['sub']).first()

    # Get all types of requests
    pending_requests = Request.query.filter_by(user_id=user.id, status='pending').all()
    returned_requests = Request.query.filter_by(user_id=user.id, status='returned').all()
    draft_requests = Request.query.filter_by(user_id=user.id, status='draft').all()
    completed_requests = Request.query.filter_by(user_id=user.id, status='completed').all()
    approved_requests = Request.query.filter_by(user_id=user.id, status='approved').all()

    return render_template('user_requests.html',
                           pending_requests=pending_requests,
                           returned_requests=returned_requests,
                           draft_requests=draft_requests,
                           completed_requests=completed_requests,
                           approved_requests=approved_requests,
                           logged_in=True)

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

# Generate FERPA PDF form
@app.route('/manager/requests/generate_ferpa', methods=['POST'])
@role_required('manager')
def generate_ferpa():
    pass

# Generate SSN/Name Change PDF Form
@app.route('/manager/requests/generate_name_ssn')
@role_required('manager')
def generate_name_ssn():
    pass


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
