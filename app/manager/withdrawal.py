from flask import session, redirect, url_for, flash
from app.manager import manager_bp
from app.models import MedicalWithdrawalRequest, User, db
from app.auth.role_required import role_required

# Approve medical withdrawal request
@manager_bp.route('/requests/withdrawal-approve/<int:id>', methods=['POST'])
@role_required('manager')
def approve_withdrawal_request(id):
    req = MedicalWithdrawalRequest.query.get_or_404(id)
    req.status = 'approved'
    
    db.session.commit()
    
    flash('Request approved successfully.', 'success')
    return redirect(url_for('manager.manage_requests'))

# Return medical withdrawal request
@manager_bp.route('/requests/withdrawal-return/<int:id>', methods=['POST'])
@role_required('manager')
def return_withdrawal_request(id):
    req = MedicalWithdrawalRequest.query.get_or_404(id)
    req.status = 'returned'
    
    db.session.commit()
    
    flash('Request returned successfully.', 'warning')
    return redirect(url_for('manager.manage_requests'))

# Reject an medical withdrawal request
@manager_bp.route('/requests/withdrawal-reject/<int:id>', methods=['POST'])
@role_required('manager')
def reject_withdrawal_request(id):
    req = MedicalWithdrawalRequest.query.get_or_404(id)
    req.status = 'rejected'
    
    db.session.commit()
    
    flash('Request rejected successfully.', 'warning')
    return redirect(url_for('manager.manage_requests'))