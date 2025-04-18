from flask import session, redirect, url_for, flash
from app.manager import manager_bp
from app.models import Request, User, db
from app.auth.role_required import role_required

# Approve info change request
@manager_bp.route('/requests/approve/<int:id>', methods=['POST'])
@role_required('manager')
def approve_request(id):
    req = Request.query.get_or_404(id)
    req.status = 'approved'
    
    db.session.commit()
    
    flash('Request approved successfully.', 'success')
    return redirect(url_for('manager.manage_requests'))

# Return info change request
@manager_bp.route('/requests/return/<int:id>', methods=['POST'])
@role_required('manager')
def return_request(id):
    req = Request.query.get_or_404(id)
    req.status = 'returned'
    
    db.session.commit()
    
    flash('Request returned successfully.', 'warning')
    return redirect(url_for('manager.manage_requests'))

# Reject an info change request
@manager_bp.route('/requests/reject/<int:id>', methods=['POST'])
@role_required('manager')
def reject_request(id):
    req = Request.query.get_or_404(id)
    req.status = 'rejected'
    
    db.session.commit()
    
    flash('Request rejected successfully.', 'warning')
    return redirect(url_for('manager.manage_requests'))