import os
from flask import render_template, session, redirect, url_for, flash, send_from_directory, current_app
from . import main_bp
from app.models import User

# Home page
@main_bp.route('/')
@main_bp.route('/home')
def home():
    if session.get('logged_in', False):
        user = User.query.filter_by(azure_id=session['user']['sub']).first()
        roles = [role.name for role in user.roles]
        return render_template('index.html', logged_in=True, roles=roles, user=session['user'])

    return render_template('index.html', logged_in=False)

# About page
@main_bp.route('/about')
def about():
    if session.get('logged_in', False):
        # Get current user and roles
        user = User.query.filter_by(azure_id=session['user']['sub']).first()
        roles = [role.name for role in user.roles]

        return render_template('about.html', logged_in=True, roles=roles)

    return render_template('about.html', logged_in=False)

# 404 handler
@main_bp.errorhandler(404)
def page_not_found(error):
    
    if session.get('logged_in', False):
        user = User.query.filter_by(azure_id=session['user']['sub']).first()
        roles = [role.name for role in user.roles]

        return render_template('404.html', logged_in=True, roles=roles)

    return render_template('404.html', logged_in=False)

# Download PDF form from requests
@main_bp.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    # Ensure the file exists within the uploads directory
    file_path = os.path.join(current_app.config['FORM_FOLDER'], filename)
    print("Form Folder: " + current_app.config['FORM_FOLDER'])
    print("Filename: " + filename)
    print("Final File Path: " + file_path)
    
    if not os.path.exists(file_path):
        flash('File not found.', 'danger')
        return redirect(url_for('user.user_requests'))

    # Serve the file for download
    return send_from_directory(directory=current_app.config['FORM_FOLDER'], path=filename, as_attachment=True)