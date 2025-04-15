from flask import session, redirect, url_for, render_template, flash
from app.manager import manager_bp
from app.models import FERPARequest, InfoChangeRequest, MedicalWithdrawalRequest, User, db
from app.auth.role_required import role_required

# Manage requests dashboard
@manager_bp.route('/requests/manage')
@role_required('manager')
def manage_requests():
    ferpa_requests = FERPARequest.query.filter(FERPARequest.status != "draft").all()
    infochange_requests = InfoChangeRequest.query.filter(InfoChangeRequest.status != "draft").all()
    withdrawal_requests = MedicalWithdrawalRequest.query.filter(MedicalWithdrawalRequest.status != "draft").all()

    # Get current user and roles
    user = User.query.filter_by(azure_id=session['user']['sub']).first()
    roles = [role.name for role in user.roles]

    return render_template('manage_requests.html', 
        ferpa_requests=ferpa_requests,
        infochange_requests=infochange_requests,
        withdrawal_requests=withdrawal_requests,
        logged_in=True, roles=roles)