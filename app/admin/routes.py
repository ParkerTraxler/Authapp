from flask import render_template, redirect, url_for, flash, session, request
from app.admin import admin_bp
from app.models import User, Role, RequestType, RequestStep, OrganizationalUnit, db
from app.auth.role_required import role_required
from app.forms import UserForm

# User management dashboard
@admin_bp.route('/dashboard')
@role_required('admin')
def admin_dashboard():
    # Get users from database
    users = User.query.all()
    
    # Get current user roles
    user = User.query.filter_by(azure_id=session['user']['sub']).first()
    roles = [role.name for role in user.roles]

    # Get request types and organizational units
    request_types = list(RequestType)
    org_units = OrganizationalUnit.query.order_by(OrganizationalUnit.name).all()
    
    return render_template('admin_dashboard.html',
        users=users,
        request_types=request_types,
        org_units=org_units,
        logged_in=True,
        roles=roles
    )

# Create new user
@admin_bp.route('/users/create', methods=['GET', 'POST'])
@role_required('admin')
def create_user():

    form = UserForm()
    
    if form.validate_on_submit():

        # Create a new user
        new_user = User(
            name=form.name.data,
            email=form.email.data,
            active=form.active.data
        )

        # Assign roles
        for role_id in form.roles.data:
            role = Role.query.get(role_id)
            if role:
                new_user.roles.append(role)

        db.session.add(new_user)
        db.session.commit()
        
        flash('User created successfully', 'success')
        return redirect(url_for('admin.admin_dashboard'))
    
    # Get current user roles
    user = User.query.filter_by(azure_id=session['user']['sub']).first()
    roles = [role.name for role in user.roles]
    
    return render_template('create_user.html', form=form, logged_in=True, roles=roles)

# Edit existing user
@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    
    if form.validate_on_submit():
        user.name = form.name.data
        user.email = form.email.data
        user.active = form.active.data

        # Update roles
        user.roles = []
        for role_id in form.roles.data:
            role = Role.query.get(role_id)
            if role:
                user.roles.append(role)

        db.session.commit()
        flash('User updated successfully.', 'success')
        return redirect(url_for('admin.admin_dashboard'))
    
    # Get current user and roles
    user = User.query.filter_by(azure_id=session['user']['sub']).first()
    roles = [role.name for role in user.roles]

    return render_template('edit_user.html', form=form, user=user, logged_in=True, roles=roles)

# Delete users
@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@role_required('admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin.admin_dashboard'))

# Deactivate users
@admin_bp.route('/users/<int:user_id>/deactivate', methods=['POST'])
@role_required('admin')
def deactivate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.active = False
    db.session.commit()
    flash('User account deactivated.', 'success')
    return redirect(url_for('admin.admin_dashboard'))

# Activate users
@admin_bp.route('/users/<int:user_id>/activate', methods=['POST'])
@role_required('admin')
def activate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.active = True
    db.session.commit()
    flash('User account activated.', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/update-approval-steps', methods=['POST'])
def update_approval_steps():
    # Get the request type from the form
    request_type_str = request.form.get('request_type')
    if not request_type_str:
        flash("Request type is required.", "danger")
        return redirect(url_for('admin.admin_dashboard'))

    # Convert string to enum
    try:
        request_type = RequestType[request_type_str]
    except KeyError:
        flash("Invalid request type.", "danger")
        return redirect(url_for('admin.admin_dashboard'))

    # Gather selected org unit IDs in order
    org_unit_ids = []
    for i in range(1, 6):  # assuming 5 steps max
        unit_id = request.form.get(f'step_{i}')
        if unit_id:
            org_unit_ids.append(int(unit_id))

    if not org_unit_ids:
        flash("At least one organizational unit must be selected.", "warning")
        return redirect(url_for('admin.admin_dashboard'))

    # Delete old steps for this request type
    RequestStep.query.filter_by(request_type=request_type).delete()

    # Insert new steps in order
    for step_number, org_unit_id in enumerate(org_unit_ids, start=1):
        new_step = RequestStep(
            request_type=request_type,
            step_number=step_number,
            org_unit_id=org_unit_id
        )
        db.session.add(new_step)

    db.session.commit()
    flash(f"Approval steps for '{request_type.name}' updated successfully.", "success")
    return redirect(url_for('admin.admin_dashboard'))