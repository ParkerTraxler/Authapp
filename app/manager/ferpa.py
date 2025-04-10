from flask import session, redirect, url_for, flash
from app.manager import manager_bp
from app.models import FERPARequest, User, db
from app.auth.role_required import role_required

# Approve a FERPA request
@manager_bp.route('/manager/requests/ferpa-approve/<int:id>', methods=['POST'])
@role_required('manager')
def approve_ferpa_request(id):
    print("In function")
    req = FERPARequest.query.get_or_404(id)
    req.status = 'approved'
    
    db.session.commit()
    
    flash('Request approved successfully.', 'success')
    return redirect(url_for('manager.manage_requests'))

# Return a FERPA request
@manager_bp.route('/requests/ferpa-return/<int:id>', methods=['POST'])
@role_required('manager')
def return_ferpa_request(id):
    req = FERPARequest.query.get_or_404(id)
    req.status = 'returned'
    
    db.session.commit()
    
    flash('Request returned successfully.', 'warning')
    return redirect(url_for('manager.manage_requests'))

# Reject a FERPA request
@manager_bp.route('/requests/ferpa-reject/<int:id>', methods=['POST'])
@role_required('manager')
def reject_ferpa_request(id):
    req = FERPARequest.query.get_or_404(id)
    req.status = 'rejected'
    
    db.session.commit()
    
    flash('Request rejected successfully.', 'warning')
    return redirect(url_for('manager.manage_requests'))