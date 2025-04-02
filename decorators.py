from functools import wraps
from flask import session, flash, redirect, url_for
from models import User

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
