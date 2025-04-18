from flask import redirect, url_for, abort
from app.models import Request, RequestType
from app.user import user_bp
from app.auth import role_required

@user_bp.route('/requests/edit/<int:request_id>')
@role_required('user')
def edit_request(request_id):
    request = Request.query.get_or_404(request_id)

    match request.request_type:
        case RequestType.FERPA:
            return redirect(url_for('edit_ferpa_request', ferpa_request_id=request_id))
        case RequestType.INFO:
            return redirect(url_for('edit_info_request', info_request_id=request_id))
        case RequestType.MEDICAL:
            return redirect(url_for('edit_withdrawal_request', withdrawal_request_id=request_id))
        case RequestType.DROP:
            return redirect(url_for('edit_drop_request', drop_request_id=request_id))
        case _:
            abort(404)