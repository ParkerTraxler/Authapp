from flask import session, redirect, url_for, render_template, flash
from app.manager import manager_bp
from app.models import Request, User, db
from app.auth.role_required import role_required

# Manage requests dashboard
@manager_bp.route('/requests/manage')
@role_required('manager')
def manage_requests():
    manager = User.query.filter_by(azure_id=session['user']['sub']).first()

    # Get requests assigned but not delegated
    requests = Request.query.filter(
        Request.current_approver_id == manager.id,
        Request.delegated_to_id == None,
        Request.status != 'draft'
    ).all()

    # Get delegated requests
    delegated_requests = Request.query.join(
        User, Request.delegated_to_id == User.id
    ).filter(
        User.unit_id == manager.unit_id,
        Request.status != 'draft'
    ).all()

    # Get current user and roles
    user = User.query.filter_by(azure_id=session['user']['sub']).first()
    roles = [role.name for role in user.roles]

    return render_template('manage_requests.html', 
        requests=requests,
        delegated_requests=delegated_requests,
        logged_in=True, 
        roles=roles)

@manager_bp.route('/requests/reports', methods=['GET'])
@role_required('manager')
def reports():
    manager = User.query.filter_by(azure_id=session['user']['sub']).first()
    roles = [role.name for role in manager.roles]

    # Get all requests for the manager's organizational unit
    unit_requests = Request.query.filter_by(current_unit_id=manager.unit_id).all()

    # Get pending approvals for the manager's unit
    pending_requests = Request.query.filter_by(current_unit_id=manager.unit_id, status='pending').all()

    # Get historical approvals for the manager's unit
    approved_requests = Request.query.filter_by(current_unit_id=manager.unit_id, status='approved').all()

    # Get rejected requests for the manager's unit
    rejected_requests = Request.query.filter_by(current_unit_id=manager.unit_id, status='rejected').all()

    print(manager.unit_id)

    return render_template(
        'reports.html',
        unit_requests=unit_requests,
        pending_requests=pending_requests,
        approved_requests=approved_requests,
        rejected_requests=rejected_requests,
        logged_in=True,
        roles=roles)