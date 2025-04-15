import os, uuid
from flask import request, session, render_template, flash, redirect, url_for, current_app
from app.models import User, StudentDropRequest, db
from app.auth.role_required import role_required
from app.forms import StudentDropForm
from app.user import user_bp
from app.utils.request_utils import allowed_file, return_choice_bool, generate_drop

@user_bp.route('/requests/student_drop', methods=['GET', 'POST'])
@role_required('user')
def student_drop_request():

    # Name/SSN change form
    form = StudentDropForm()

    # Get current user
    user = User.query.filter_by(azure_id=session['user']['sub']).first()

    if not form.validate_on_submit():
        print(form.errors)

    if form.validate_on_submit():
        # Ensure the user uploaded a signature
        if 'signature' not in request.files:
            flash('Signature was not uploaded.', 'danger')
            return render_template('medical_withdrawal.html', form=form, logged_in=True)

        file = request.files['signature']
        if file.filename == '':
            flash('No file selected for signature.', 'danger')
            return render_template('medical_withdrawal.html', form=form, logged_in=True)

        # Check the file is allowed
        if file and allowed_file(file.filename):
            
            # Generate a unique name for the image
            unique_filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()

            # Save file with new name
            filepath = os.path.normpath(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
            file.save(filepath)

            latex_path = filepath.replace("\\", "/")

            # Get user id from session
            user = User.query.filter_by(azure_id=session['user']['sub']).first()
            user_id = user.id

            # Create dictionary to pass to function
            data = {
                "NAME": form.name.data,
                "PEOPLESOFT": form.peoplesoft_id.data,
                "BIRTHDATE": str(form.birthdate.data),
                "TERMYEAR": form.term_year.data,
                "SUBJECT": form.subject.data,
                "NUMBER": form.number.data,
                "SECTION": form.section.data,
                "SIGNATURE": latex_path,
                "DATE": str(form.date.data)
            }

            pdf_link = generate_drop(data)

            # Pending or draft?
            if form.is_draft.data:
                status = "draft"
            else: status = "pending"

            new_drop_request = StudentDropRequest(
                user_id=user_id,
                status=status,
                pdf_link=pdf_link,
                sig_link=unique_filename,
                name=data['NAME'],
                peoplesoft_id=data['PEOPLESOFT'],
                birthdate=data['BIRTHDATE'],
                term_year=data['TERMYEAR'],
                subject=data['SUBJECT'],
                number=data['NUMBER'],
                section=data['SECTION'],
                date=data['DATE']
            )

            db.session.add(new_drop_request)
            db.session.commit()

            return redirect(url_for('user.user_requests'))
        
    # Get user roles
    roles = [role.name for role in user.roles]

    return render_template('student_drop.html', form=form, logged_in=True, roles=roles)

# Edit a medical withdrawal request
@user_bp.route('/requests/edit-drop-request/<drop_request_id>', methods=['GET', 'POST'])
@role_required('user')
def edit_drop_request(drop_request_id):
    # Ensure the user is logged in, get roles
    if not session.get('logged_in', False):
        return redirect(url_for("auth.login"))
    
    # Ensure the request exists
    drop_request = StudentDropRequest.query.get_or_404(drop_request_id)
    if not drop_request:
        flash('Student drop request was not found.', 'error')
        return redirect(url_for("user.user_requests"))
    
    if drop_request.status == "pending":
        flash('Student drop request was already submitted. No further modifications are permitted until approved by a manager.')
        return redirect(url_for("user.user_requests"))
    elif drop_request.status == "approved":
        flash('Student drop request was already approved. No further modifications are allowed.')
        return redirect(url_for("user.user_requests"))
    elif drop_request.status == "rejected":
        flash('Student drop request was rejected. No further modifications are allowed.')
        return redirect(url_for("user.user_requests"))
    
    # Create form, populate with user data
    form = StudentDropForm()

    # Populate form data from database
    if request.method == 'GET':
        form.name.data = drop_request.name
        form.peoplesoft_id.data = drop_request.peoplesoft_id

        form.term_year.data = drop_request.term_year

        form.subject.data = drop_request.subject
        form.number.data = drop_request.number
        form.section.data = drop_request.section

        form.date.data = drop_request.date

    if form.validate_on_submit():
        # Ensure the user uploaded a signature
        if 'signature' not in request.files:
            flash('Signature was not uploaded.', 'danger')
            return render_template('medical_withdrawal.html', form=form, logged_in=True)

        file = request.files['signature']
        if file.filename == '':
            flash('No file selected for signature.', 'danger')
            return render_template('medical_withdrawal.html', form=form, logged_in=True)

        # Check the file is allowed
        if file and allowed_file(file.filename):
            
            # Generate a unique name for the image
            unique_filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()

            # Save file with new name
            filepath = os.path.normpath(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
            file.save(filepath)

            latex_path = filepath.replace("\\", "/")

            # Get user id from session
            user = User.query.filter_by(azure_id=session['user']['sub']).first()
            user_id = user.id

            # Create dictionary to pass to function
            data = {
                "NAME": form.name.data,
                "PEOPLESOFT": form.peoplesoft_id.data,
                "TERMYEAR": form.term_year.data,
                "SUBJECT": form.subject.data,
                "NUMBER": form.number.data,
                "SECTION": form.section.data,
                "SIGNATURE": latex_path,
                "DATE": str(form.date.data)
            }

            pdf_link = generate_drop(data)

            # Pending or draft?
            if form.is_draft.data:
                status = "draft"
            else: status = "pending"

            # Update attribute values of request
            drop_request.status = status
            drop_request.pdf_link = pdf_link
            drop_request.name = data['NAME']
            drop_request.peoplesoft_id = data['PEOPLESOFT']
            drop_request.term_year = data['TERMYEAR']
            drop_request.subject = data['SUBJECT']
            drop_request.number = data['NUMBER']
            drop_request.section = data['SECTION']
            drop_request.date = form.date.data

            db.session.commit()

            return redirect(url_for('user.user_requests'))

    # Get current user and roles
    user = User.query.filter_by(azure_id=session['user']['sub']).first()
    roles = [role.name for role in user.roles]

    return render_template('medical_withdrawal.html', form=form, logged_in=True, roles=roles)