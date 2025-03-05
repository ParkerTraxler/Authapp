import os, secrets
from dotenv import load_dotenv
from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length

# load environment variables
load_dotenv()

app = Flask(__name__)

# connects the app to the sql database and secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:D0Ge59PDT@localhost/auth_app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'verysecretkey123'

db = SQLAlchemy(app)

# OAuth
oauth = OAuth(app)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'flask_'
app.config['SESSION_FILE_DIR'] = './.flask_session'
Session(app)

microsoft = oauth.register(
    name = 'microsoft',
    client_id = os.getenv('AZURE_CLIENT_ID'),
    client_secret = os.getenv('AZURE_CLIENT_SECRET'),
    server_metadata_url = f'https://login.microsoftonline.com/{os.getenv("AZURE_TENANT_ID")}/v2.0/.well-known/openid-configuration',
    client_kwargs = {'scope': 'User.Read openid profile offline_access'}
)

# flask login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# the model for the database table
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False) # should be hashed later
    firstName = db.Column(db.String(100), nullable=True)
    lastName = db.Column(db.String(100), nullable=True)
    active = db.Column(db.Boolean())
    role = db.Column(db.String(50), nullable=False, default='basicuser')

    @property
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return self.status == 'active'
    
    def is_admin(self):
        return self.role == 'administrator'

# creates the database tables and admin user
with app.app_context():
    db.create_all()

    admin_user = User.query.filter_by(email="admin").first()
    if not admin_user:
        admin_user = User(email="admin", password="password", active=True, firstName="admin", role="administrator")
        db.session.add(admin_user)
    
    db.session.commit()


# login form class (flask-wtf)
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

# update profile form class for manage-account
class UpdateProfileForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Length(max=50)])
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=50)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(max=50)])
    submit = SubmitField("Update Profile")

class CreateUserForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Length(max=50)])
    password = StringField("Password", validators=[DataRequired(), Length(min=8)])
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=100)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(max=100)])
    active = BooleanField("Active", default=True)
    role = SelectField("Role", choices=[("basicuser", "Basic User"), ("administrator", "Administrator")])
    submit = SubmitField('Create User')

class EditUserForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Length(max=50)])
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=100)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(max=100)])
    active = BooleanField("Active")
    role = SelectField("Role", choices=[("basicuser", "Basic User"), ("administrator", "Administrator")])
    submit = SubmitField("Update User")


# loads the user
@login_manager.user_loader
def load_user(user_id):
    return(User.query.get(int(user_id)))


# login route, logs in the user, does not take input yet
@app.route('/login', methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    form = LoginForm()

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Find the user by the email
        user = User.query.filter_by(email=email).first()

        # disallow deactivated users
        if user and not user.active:
            return "Your account has been deactivated. Please contact an administrator for reactivation."
        
        # check 
        if user and user.password == password:
            login_user(user)
            return(redirect(url_for('home')))
        
        return("Invalid credentials.")
    
    return(render_template('login.html', form=form))

# microsoft login route
@app.route('/login-microsoft')
def login_microsoft():

    redirect_uri = url_for('getAToken', _external=True)
    return(microsoft.authorize_redirect(redirect_uri))

@app.route('/getAToken')
def getAToken():
    # retrieve the access token from Microsoft OAuth
    token = microsoft.authorize_access_token()

    # store the token in the session for future use
    session['access_token'] = token.get('access_token')
    session['refresh_token'] = token.get('refresh_token')

    # get user information from the Microsoft Graph API, currently we're doing nothing with it
    user_info = microsoft.get('https://graph.microsoft.com/v1.0/me').json()
    
    user = User.query.filter_by(email=user_info.get('userPrincipalName')).first()

    # disallow deactivated users
    if user and not user.active:
        return "Your account has been deactivated. Please contact an administrator for reactivation."

    # if the user does not exist, create a new one
    if user is None:
        user = User(email=user_info.get('userPrincipalName'), firstName=user_info['givenName'], lastName=user_info['surname'], password='')
        db.session.add(user)
        db.session.commit()
    
    # Log the user in
    login_user(user)

    # Let Flask-Login know who is logged in
    session['user_id'] = user.id

    #Redirect to the home page
    return(redirect(url_for('home')))

# logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return(redirect(url_for('home')))

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if not current_user.is_authenticated:
        flash("You must be logged in to access the admin dashboard.")
        return redirect(url_for('home'))
    if current_user.role != "administrator":
        flash("You must be an admin to access the admin dashboard.")
        return redirect(url_for('home'))
    
    users = User.query.all()
    form = CreateUserForm()

    if form.validate_on_submit():
        new_user = User(
            email = form.email.data.strip(),
            password = form.password.data.strip(),
            firstName = form.first_name.data.strip(),
            lastName = form.last_name.data.strip(),
            active = form.active.data,
            role = form.role.data
        )

        db.session.add(new_user)
        db.session.commit()
        flash(f"User {new_user.email} has been created successfully!")
        
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        action = request.form.get('action')

        user = User.query.get(user_id)

        if action == 'deactivate':
            user.active = False
            flash(f"User {user.email} has been deactivated.")
        elif action == 'activate':
            user.active = True
            flash(f"User {user.email} has been activated")
        elif action == 'update_role':
            new_role = request.form.get('new_role')
            user.role = new_role
            flash(f"User {user.email}'s role has been updated to {new_role}")

        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_dashboard.html', users=users, form=form)

@app.route("/admin/edit/<int:user_id>", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    if not current_user.is_authenticated or current_user.role != "administrator":
        flash("You must be an admin to edit users.")
        return redirect(url_for("admin_dashboard"))
    
    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)

    if form.validate_on_submit():
        user.email = form.email.data.strip()
        user.firstName = form.first_name.data.strip()
        user.lastName = form.last_name.data.strip()
        user.active = form.active.data
        user.role = form.role.data
        db.session.commit()
        flash(f"User {user.email} has been updated successfully!")
        return redirect(url_for("admin_dashboard"))
    
    return render_template("edit_user.html", form=form, user=user)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    
    form = UpdateProfileForm()

    if form.validate_on_submit():
        current_user.firstName = form.first_name.data.strip()
        current_user.lastName = form.last_name.data.strip()
        current_user.email = form.email.data.strip()
        db.session.commit()
        return(redirect(url_for('profile')))
    
    # Prefills the fields with existing user data
    form.first_name.data = current_user.firstName
    form.last_name.data = current_user.lastName
    form.email.data = current_user.email

    return(render_template('profile.html', form=form))

# home route
@app.route('/')
@app.route('/home')
def home():
    return(render_template('index.html'))

# 404 route
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html')

if __name__ == '__main__':

    app.run(debug=True)