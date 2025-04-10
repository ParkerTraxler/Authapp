from flask import redirect, render_template, session, flash, url_for, request
from app.forms import ProfileForm
from app.models import User, FERPARequest, InfoChangeRequest, db
from app.user import user_bp
from app.auth.role_required import role_required

@user_bp.route('/profile', methods=['GET', 'POST'])
@role_required('user')
def profile():  
    # Ensure the user is logged in, get roles
    if not session.get('logged_in', False):
        return redirect(url_for("auth.login"))
    
    # Ensure the user exists
    user = User.query.filter_by(azure_id=session['user']['sub']).first()
    if not user:
        flash('User not found', 'error')
        return redirect(url_for("main.home"))

    # Create form, populate with user data
    form = ProfileForm()

    # Manually populate the form
    if request.method == 'GET':
        form.name.data = user.name
        form.email.data = user.email

    # Handle form submission
    if form.validate_on_submit():
        # Update user info from form data
        user.name = form.name.data
        user.email = form.email.data

        # Update databasem, send message to user
        try:
            db.session.commit()
            flash('Profile updated successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')

        return redirect(url_for("user.profile"))
    
    # Get current user and roles
    user = User.query.filter_by(azure_id=session['user']['sub']).first()
    roles = [role.name for role in user.roles]

    return render_template('profile.html', form=form, logged_in=True, roles=roles)

@user_bp.route('/requests/manage')
@role_required('user')
def user_requests():
   
    # Get user id for requests
    user = User.query.filter_by(azure_id=session['user']['sub']).first()

    # Get all types of requests
    ferpa_requests = FERPARequest.query.filter_by(user_id=user.id).all()
    infochange_requests = InfoChangeRequest.query.filter_by(user_id=user.id)

    # Get current user and roles
    user = User.query.filter_by(azure_id=session['user']['sub']).first()
    roles = [role.name for role in user.roles]

    return render_template('user_requests.html',
        ferpa_requests=ferpa_requests,
        infochange_requests=infochange_requests,
        logged_in=True, roles=roles)