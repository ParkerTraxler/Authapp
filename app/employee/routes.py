from . import employee_bp
from app.auth.role_required import role_required
from app.models import User, Request
from flask import render_template, session

@employee_bp.route('/requests/delegated')
@role_required('employee')  # or whatever role check applies
def delegated_requests():
    employee = User.query.filter_by(azure_id=session['user']['sub']).first()
    roles = [role.name for role in employee.roles]

    requests = Request.query.filter_by(delegated_to_id=employee.id).filter(Request.status != 'draft').all()

    return render_template('employee_requests.html', requests=requests, roles=roles, logged_in=True)