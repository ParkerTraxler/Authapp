from flask import session, redirect, url_for, flash, request, render_template
from app.manager import manager_bp
from app.models import Request, User, db
from app.auth.role_required import role_required
from app.forms import DelegateRequestForm

# Approve request
@manager_bp.route('/requests/approve/<int:id>', methods=['POST'])
@role_required('manager', 'employee')
def approve_request(id):
    req = Request.query.get_or_404(id)
    manager = User.query.filter_by(azure_id=session['user']['sub']).first()

    if req.current_approver_id != manager.id:
        flash('You are not authorized to approve this request.', 'danger')
        return redirect(url_for('manager.manage_requests'))
    
    if req.current_unit and req.current_unit.parent:
        parent_unit = req.current_unit.parent
        req.current_unit_id = parent_unit.id
        req.current_approver_id = parent_unit.manager_id
        req.delegated_to_id = None
        req.modified_at = db.func.now()
        flash(f'The request has been forwarded to {parent_unit.name} for further approval.', 'info')
    else:
        req.status = 'approved'
        req.current_approver_id = None
        flash('The request has been approved successfully.', 'success')

    db.session.commit()
    return redirect(url_for('manager.manage_requests'))

# Return request
@manager_bp.route('/requests/return/<int:id>', methods=['POST'])
@role_required('manager', 'employee')
def return_request(id):
    req = Request.query.get_or_404(id)
    req.status = 'returned'
    req.modified_at = db.func.now()
    
    db.session.commit()
    
    flash('Request returned successfully.', 'warning')
    return redirect(url_for('manager.manage_requests'))

# Reject a request
@manager_bp.route('/requests/reject/<int:id>', methods=['POST'])
@role_required('manager', 'employee')
def reject_request(id):
    req = Request.query.get_or_404(id)
    req.status = 'rejected'
    req.modified_at = db.func.now()
    
    db.session.commit()
    
    flash('Request rejected successfully.', 'warning')
    return redirect(url_for('manager.manage_requests'))

# Delegate a request to an employee
@manager_bp.route('/requests/delegate/<int:id>', methods=['POST', 'GET'])
@role_required('manager')
def delegate_request(id):
    req = Request.query.get_or_404(id)
    manager = User.query.filter_by(azure_id=session['user']['sub']).first()

    # Ensure request belongs to the manager's unit
    if req.current_approver_id != manager.id:
        flash('You are not authorized to delegate this request.', 'danger')
        return redirect(url_for('manager.manage_requests'))
    
    # Get employees in the manager's OU
    employees = User.query.filter_by(unit_id=manager.unit_id, active=True).all()

    # Populate form with employees
    form = DelegateRequestForm()
    form.employee.choices = [(employee.id, employee.name) for employee in employees]

    if form.validate_on_submit():
        # Delegate request to selected employee
        req.current_approver_id = form.employee.data
        req.delegated_to_id = form.employee.data
        db.session.commit()
        
        flash('Request delegated successfully.', 'success')
        return redirect(url_for('manager.manage_requests'))
    
    # Get current user and roles
    user = User.query.filter_by(azure_id=session['user']['sub']).first()
    roles = [role.name for role in user.roles]
    
    return render_template('delegate_request.html', form=form, request=req, logged_in=True, roles=roles)
    
