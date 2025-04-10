from flask import render_template, redirect, url_for, flash, session
from app.admin import admin_bp
from app.models import User, Role, db
from app.auth.role_required import role_required
from app.forms import UserForm

# User management dashboard
@admin_bp.route('/users')
@role_required('admin')
def manage_users():
    # Get users from database
    users = User.query.all()
    
    # Get current user roles
    user = User.query.filter_by(azure_id=session['user']['sub']).first()
    roles = [role.name for role in user.roles]
    
    return render_template('manage_users.html', users=users, logged_in=True, roles=roles)

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
        return redirect(url_for('admin.manage_users'))
    
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
        return redirect(url_for('admin.manage_users'))
    
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
    return redirect(url_for('admin.manage_users'))

# Deactivate users
@admin_bp.route('/users/<int:user_id>/deactivate', methods=['POST'])
@role_required('admin')
def deactivate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.active = False
    db.session.commit()
    flash('User account deactivated.', 'success')
    return redirect(url_for('admin.manage_users'))

# Activate users
@admin_bp.route('/users/<int:user_id>/activate', methods=['POST'])
@role_required('admin')
def activate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.active = True
    db.session.commit()
    flash('User account activated.', 'success')
    return redirect(url_for('admin.manage_users'))