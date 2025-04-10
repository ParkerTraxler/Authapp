from flask import session, redirect, url_for, flash
from app.manager import manager_bp
from app.models import InfoChangeRequest, User, db
from app.auth.role_required import role_required

# Approve info change request
@manager_bp.route('/requests/infochange-approve/<int:id>', methods=['POST'])
@role_required('manager')
def approve_infochange_request(id):
    req = InfoChangeRequest.query.get_or_404(id)
    req.status = 'approved'
    
    db.session.commit()
    
    flash('Request approved successfully.', 'success')
    return redirect(url_for('manager.manage_requests'))

# Return info change request
@manager_bp.route('/requests/infochange-return/<int:id>', methods=['POST'])
@role_required('manager')
def return_infochange_request(id):
    req = InfoChangeRequest.query.get_or_404(id)
    req.status = 'returned'
    
    db.session.commit()
    
    flash('Request returned successfully.', 'warning')
    return redirect(url_for('manager.manage_requests'))

# Reject an info change request
@manager_bp.route('/requests/infochange-reject/<int:id>', methods=['POST'])
@role_required('manager')
def reject_infochange_request(id):
    req = InfoChangeRequest.query.get_or_404(id)
    req.status = 'rejected'
    
    db.session.commit()
    
    flash('Request rejected successfully.', 'warning')
    return redirect(url_for('manager.manage_requests'))