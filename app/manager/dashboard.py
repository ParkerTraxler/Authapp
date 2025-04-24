from flask import session, redirect, url_for, render_template, flash
from app.manager import manager_bp
from app.models import Request, User, OrganizationalUnit, db
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
def unit_report():
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

    # Check if the current user is manager of the root OU
    root_unit = OrganizationalUnit.query.filter_by(name="Academic and Student Services").first()
    is_root = manager.unit_id == root_unit.id

    return render_template(
        'unit_report.html',
        unit_requests=unit_requests,
        pending_requests=pending_requests,
        approved_requests=approved_requests,
        rejected_requests=rejected_requests,
        is_root=is_root,
        logged_in=True,
        roles=roles)

@manager_bp.route('/requests/reports/organization', methods=['GET'])
@role_required('manager')
def org_report():
    manager = User.query.filter_by(azure_id=session['user']['sub']).first()

    # Only allow access if manager is head of root unit
    root_unit = OrganizationalUnit.query.filter_by(name="Academic and Student Services").first()
    if not root_unit or manager.unit_id != root_unit.id:
        flash("You do not have access to organizational-level reports.", "danger")
        return redirect(url_for('manager.unit_report'))

    roles = [role.name for role in manager.roles]

    all_requests = Request.query.all()
    pending_requests = Request.query.filter_by(status='pending').all()
    approved_requests = Request.query.filter_by(status='approved').all()
    rejected_requests = Request.query.filter_by(status='rejected').all()

    return render_template(
        'organization_report.html',
        all_requests=all_requests,
        pending_requests=pending_requests,
        approved_requests=approved_requests,
        rejected_requests=rejected_requests,
        logged_in=True,
        roles=roles
    )
