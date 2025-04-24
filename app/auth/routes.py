from flask import redirect, render_template, url_for, session, flash, request, current_app
from . import auth_bp
from app.msal_config import get_msal_app
from app.models import User, Role, OrganizationalUnit, db

# Azure login
@auth_bp.route('/login/azure')
def login_azure():
    app_instance = get_msal_app()
    print(f"Redirect URI: {current_app.config['REDIRECT_URI']}")
    auth_url = app_instance.get_authorization_request_url(current_app.config['SCOPE'], redirect_uri=current_app.config['REDIRECT_URI'])
    return redirect(auth_url)

# Local login
@auth_bp.route('/login/local', methods=['GET', 'POST'])
def login_local():
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']

        user = User.query.filter_by(user_id=user_id).first()
        if user and user.check_password(password):
            session['user'] = {
                'sub': user.azure_id,
                'name': user.name,
                'preferred_username': user.email
            }
            session['logged_in'] = True
            return redirect(url_for('main.home'))

        flash('Invalid credentials', 'danger')
    return render_template('login_local.html')

# Retreive access token from Azure
@auth_bp.route('/get_token')
def get_token():
    app_instance = get_msal_app()

    if "code" in request.args:
        # Get token from code
        result = app_instance.acquire_token_by_authorization_code(
            request.args['code'], current_app.config['SCOPE'], redirect_uri=current_app.config['REDIRECT_URI']
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
                    return redirect(url_for("main.home"))
                
                # Redirect to setup if first login
                # if existing_user.first_login:
                    # return redirect(url_for('auth.setup_account'))

                # Store user data in session
                session['user'] = user_claims
                session['logged_in'] = True

                return redirect(url_for("main.home"))
            else:
                # Every new user gets user role, check if they're the first user
                user_role = Role.query.filter_by(name="user").first()
                user_count = User.query.count()

                # Create new user
                user = User(
                    azure_id=user_claims['sub'],
                    name=user_claims.get('name'),
                    email=user_claims.get('preferred_username'),
                    roles=[user_role]
                )

                # Commit new user to database
                db.session.add(user)
                db.session.commit()

                # If first user, give all roles and assign as manager of top unit
                if user_count == 0:
                    top_unit = OrganizationalUnit.query.filter_by(name="Academic and Student Services").first()
                    top_unit.manager = user
                    db.session.commit()

                # Store user data in session and redirect user to home
                session['user'] = user_claims
                session['logged_in'] = True

                # Redirect to setup if first login
                if user.first_login:
                    return redirect(url_for('auth.setup_account'))

                return redirect(url_for("main.home"))
    
    return "Login failed", 401

@auth_bp.route('/setup-account', methods=['GET', 'POST'])
def setup_account():
    if request.method == 'POST':
        cougarnet_id = request.form['user_id']
        password = request.form['password']

        if not cougarnet_id.isdigit() or len(cougarnet_id) != 6:
            flash('User ID must be a 6-digit number.', 'danger')
            return render_template('setup_account.html')

        if User.query.filter_by(cougarnet_id=cougarnet_id).first():
            flash('That ID is already taken.', 'danger')
            return render_template('setup_account.html')

        user = User.query.filter_by(azure_id=session['user']['sub']).first()
        user.cougarnet_id = cougarnet_id
        user.set_password(password)
        user.first_login = False
        db.session.commit()

        flash('Setup complete. You can now login using your 6-digit ID.', 'success')
        return redirect(url_for('main.home'))

    return render_template('setup_account.html')

# Log out of account, clear token
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("main.home"))

# 404 handler
@auth_bp.errorhandler(404)
def page_not_found(error):
    
    if session.get('logged_in', False):
        user = User.query.filter_by(azure_id=session['user']['sub']).first()
        roles = [role.name for role in user.roles]

        return render_template('404.html', logged_in=True, roles=roles)

    return render_template('404.html', logged_in=False)