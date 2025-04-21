from flask import redirect, render_template, url_for, session, flash, request, current_app
from . import auth_bp
from app.msal_config import get_msal_app
from app.models import User, Role, db

# User login
@auth_bp.route('/login')
def login():
    app_instance = get_msal_app()
    print(f"Redirect URI: {current_app.config['REDIRECT_URI']}")
    auth_url = app_instance.get_authorization_request_url(current_app.config['SCOPE'], redirect_uri=current_app.config['REDIRECT_URI'])
    return redirect(auth_url)

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

                # Store user data in session
                session['user'] = user_claims
                session['logged_in'] = True

                return redirect(url_for("main.home"))
            else:
                # Every new user gets user role
                user_role = Role.query.filter_by(name="user").first()

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
                
                # Store user data in session and redirect user to home
                session['user'] = user_claims
                session['logged_in'] = True
                return redirect(url_for("main.home"))
    
    return "Login failed", 401

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