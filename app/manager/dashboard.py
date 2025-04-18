from flask import session, redirect, url_for, render_template, flash
from app.manager import manager_bp
from app.models import Request, User, db
from app.auth.role_required import role_required

# Manage requests dashboard
@manager_bp.route('/requests/manage')
@role_required('manager')
def manage_requests():
    requests = Request.query.filter(Request.status != "draft").all()

    # Get current user and roles
    user = User.query.filter_by(azure_id=session['user']['sub']).first()
    roles = [role.name for role in user.roles]

    return render_template('manage_requests.html', 
        requests=requests,
        logged_in=True, roles=roles)