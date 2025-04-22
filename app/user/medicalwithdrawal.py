import os, uuid
from datetime import datetime
from flask import request, session, render_template, flash, redirect, url_for, current_app
from app.models import User, Request, RequestType, OrganizationalUnit, db
from app.auth.role_required import role_required
from app.forms import MedicalWithdrawalForm
from app.user import user_bp
from app.utils.request_utils import allowed_file, return_choice_bool, generate_withdrawal

@user_bp.route('/requests/medical_withdrawal', methods=['GET', 'POST'])
@role_required('user')
def medical_withdrawal_request():

    # Name/SSN change form
    form = MedicalWithdrawalForm()

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

            # Create dictionary to pass to function
            data = {
                "NAME": form.name.data,
                "PEOPLESOFT": form.peoplesoft_id.data,
                "COLLEGE": form.college.data,
                "DEGREE": form.degree.data,
                "ADDRESS": form.address.data,
                "CITY": form.city.data,
                "STATE": form.state.data,
                "ZIPCODE": form.zip_code.data,
                "PHONE": form.phone.data,
                "EMAIL": form.email.data,
                "TERMYEAR": form.term_year.data,
                "LASTATTENDED": str(form.last_attended.data),
                "REASON": form.reason.data,
                "DETAILS": form.details.data,
                "FINANCIALASSISTANCE": return_choice_bool(form.financial_assistance.data),
                "HEALTHINSURANCE": return_choice_bool(form.uh_health_insurance.data),
                "CAMPUSHOUSING": return_choice_bool(form.campus_housing.data),
                "VISASTATUS": return_choice_bool(form.visa_status.data),
                "GIBILL": return_choice_bool(form.gi_bill_benefits.data),
                "SUBJECT": form.subject.data,
                "NUMBER": form.number.data,
                "SECTION": form.section.data,
                "SIGNATURE": latex_path,
                "INITIAL": form.initial.data,
                "DATE": str(form.date.data)
            }

            pdf_link = generate_withdrawal(data)

            # Pending or draft?
            if form.is_draft.data: status = "draft"
            else: status = "pending"

            # Ensure organizational unit and manager exist
            medical_unit = OrganizationalUnit.query.filter_by(name='Health and Wellness').first()
            if not medical_unit or not medical_unit.manager_id:
                flash('Health and Wellness unit not found or no manager assigned.', 'error')
                return redirect(url_for('user.user_requests'))

            # Create new request
            new_request = Request(
                user_id=user.id,
                status=status,
                request_type=RequestType.MEDICAL,
                pdf_link=pdf_link,
                sig_link=unique_filename,
                form_data=data,
                current_approver_id=medical_unit.manager_id,
                current_unit_id=medical_unit.id
            )

            db.session.add(new_request)
            db.session.commit()

            return redirect(url_for('user.user_requests'))
        
    # Get user roles
    roles = [role.name for role in user.roles]

    return render_template('medical_withdrawal.html', form=form, logged_in=True, roles=roles)

# Edit a medical withdrawal request
@user_bp.route('/requests/edit-withdrawal-request/<withdrawal_request_id>', methods=['GET', 'POST'])
@role_required('user')
def edit_withdrawal_request(withdrawal_request_id):
    # Ensure the user is logged in, get roles
    if not session.get('logged_in', False):
        return redirect(url_for("auth.login"))
    
    # Ensure the request exists
    withdrawal_request = Request.query.get_or_404(withdrawal_request_id)
    if not withdrawal_request:
        flash('Withdrawal request was not found.', 'error')
        return redirect(url_for("user.user_requests"))
    
    if withdrawal_request.status == "pending":
        flash('Withdrawal request was already submitted. No further modifications are permitted until approved by a manager.')
        return redirect(url_for("user.user_requests"))
    elif withdrawal_request.status == "approved":
        flash('Withdrawal request was already approved. No further modifications are allowed.')
        return redirect(url_for("user.user_requests"))
    elif withdrawal_request.status == "rejected":
        flash('Withdrawal request was rejected. No further modifications are allowed.')
        return redirect(url_for("user.user_requests"))
    
    # Create form, populate with user data
    form = MedicalWithdrawalForm()
    data = withdrawal_request.form_data

    choices = {'FINANCIALASSISTANCE': False,
                'HEALTHINSURANCE': False,
                'CAMPUSHOUSING': False,
                'VISASTATUS': False,
                'GIBILL': False}
    
    choices = {opt: data.get(opt) == "Yes" for opt in choices}

    if request.method == 'GET':
        form.name.data = data['NAME']
        form.peoplesoft_id.data = data['PEOPLESOFT']
        form.college.data = data['COLLEGE']
        form.degree.data = data['DEGREE']

        form.address.data = data['ADDRESS']
        form.city.data = data['CITY']
        form.state.data = data['STATE']
        form.zip_code.data = data['ZIPCODE']
        form.phone.data = data['PHONE']
        form.email.data = data['EMAIL']

        form.term_year.data = data['TERMYEAR']
        form.last_attended.data = data['LASTATTENDED']

        form.reason.data = data['REASON']
        form.details.data = data['DETAILS']

        form.financial_assistance.data = choices['FINANCIALASSISTANCE']
        form.uh_health_insurance.data = choices['HEALTHINSURANCE']
        form.campus_housing.data = choices['CAMPUSHOUSING']
        form.visa_status.data = choices['VISASTATUS']
        form.gi_bill_benefits.data = choices['GIBILL']

        form.subject.data = data['SUBJECT']
        form.number.data = data['NUMBER']
        form.section.data = data['SECTION']

        form.date.data = form.date.data = datetime.strptime(data['DATE'], '%Y-%m-%d').date()

        form.initial.data = data['INITIAL']

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

            # Create dictionary to pass to function
            new_data = {
                "NAME": form.name.data,
                "PEOPLESOFT": form.peoplesoft_id.data,
                "COLLEGE": form.college.data,
                "DEGREE": form.degree.data,
                "CITY": form.city.data,
                "STATE": form.state.data,
                "ZIPCODE": form.zip_code.data,
                "PHONE": form.phone.data,
                "EMAIL": form.email.data,
                "TERMYEAR": form.term_year.data,
                "LASTATTENDED": str(form.last_attended.data),
                "REASON": form.reason.data,
                "DETAILS": form.details.data,
                "FINANCIALASSISTANCE": return_choice_bool(form.financial_assistance.data),
                "HEALTHINSURANCE": return_choice_bool(form.uh_health_insurance.data),
                "CAMPUSHOUSING": return_choice_bool(form.campus_housing.data),
                "VISASTATUS": return_choice_bool(form.visa_status.data),
                "GIBILL": return_choice_bool(form.gi_bill_benefits.data),
                "SUBJECT": form.subject.data,
                "NUMBER": form.number.data,
                "SECTION": form.section.data,
                "INITIAL": form.initial.data,
                "SIGNATURE": latex_path,
                "DATE": str(form.date.data)
            }

            pdf_link = generate_withdrawal(new_data)

            # Pending or draft?
            if form.is_draft.data: status = "draft"
            else: status = "pending"

            # Update attribute values of request
            withdrawal_request.status = status
            withdrawal_request.pdf_link = pdf_link
            withdrawal_request.form_data = new_data

            db.session.commit()

            return redirect(url_for('user.user_requests'))

    # Get current user and roles
    user = User.query.filter_by(azure_id=session['user']['sub']).first()
    roles = [role.name for role in user.roles]

    return render_template('medical_withdrawal.html', form=form, logged_in=True, roles=roles)