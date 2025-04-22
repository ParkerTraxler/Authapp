from functools import wraps
from flask import request, redirect, session, url_for, flash
from app.models import User

def role_required(*role_names):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in', False):
                return redirect(url_for("auth.login", next=request.url))

            user = User.query.filter_by(azure_id=session['user']['sub']).first()

            if not user or not any(user.has_role(role) for role in role_names):
                flash('You do not have permission to access this page', 'danger')
                return redirect(url_for("main.home"))

            return f(*args, **kwargs)
        return decorated_function
    return decorator
