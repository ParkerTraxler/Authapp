import os, uuid
from flask import request, session, render_template, flash, redirect, url_for, current_app
from app.models import User, MedicalWithdrawalRequest, db
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

            # Get user id from session
            user = User.query.filter_by(azure_id=session['user']['sub']).first()
            user_id = user.id

            # Create dictionary to pass to function
            data = {
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
                "SIGNATURE": latex_path,
                "INITIAL": form.initial.data,
                "DATE": str(form.date.data)
            }

            pdf_link = generate_withdrawal(data)

            # Pending or draft?
            if form.is_draft.data:
                status = "draft"
            else: status = "pending"

            new_medical_request = MedicalWithdrawalRequest(
                user_id=user_id,
                status=status,
                pdf_link=pdf_link,
                sig_link=unique_filename,
                name=data['NAME'],
                peoplesoft_id=data['PEOPLESOFT'],
                college=data['COLLEGE'],
                degree=data['DEGREE'],
                city=data['CITY'],
                state=data['STATE'],
                zip_code=data['ZIPCODE'],
                phone=data['PHONE'],
                email=data['EMAIL'],
                term_year=data['TERMYEAR'],
                last_attended=data['LASTATTENDED'],
                reason=data['REASON'],
                details=data['DETAILS'],
                financial_assistance=form.financial_assistance.data,
                uh_health_insurance=form.uh_health_insurance.data,
                campus_housing=form.campus_housing.data,
                visa_status=form.visa_status.data,
                gi_bill_benefits=form.gi_bill_benefits.data,
                subject=data['SUBJECT'],
                number=data['NUMBER'],
                section=data['SECTION'],
                initial=data['INITIAL'],
                date=data['DATE']
            )

            db.session.add(new_medical_request)
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
    withdrawal_request = MedicalWithdrawalRequest.query.get_or_404(withdrawal_request_id)
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

    # Populate form data from database
    if request.method == 'GET':
        form.name.data = withdrawal_request.name
        form.peoplesoft_id.data = withdrawal_request.peoplesoft_id
        form.college.data = withdrawal_request.college
        form.degree.data = withdrawal_request.degree

        form.city.data = withdrawal_request.city
        form.state.data = withdrawal_request.state
        form.zip_code.data = withdrawal_request.zip_code
        form.phone.data = withdrawal_request.phone
        form.email.data = withdrawal_request.email

        form.term_year.data = withdrawal_request.term_year
        form.last_attended.data = withdrawal_request.last_attended

        form.reason.data = withdrawal_request.reason
        form.details.data = withdrawal_request.details

        form.financial_assistance.data = withdrawal_request.financial_assistance
        form.uh_health_insurance.data = withdrawal_request.uh_health_insurance
        form.campus_housing.data = withdrawal_request.campus_housing
        form.visa_status.data = withdrawal_request.visa_status
        form.gi_bill_benefits.data = withdrawal_request.gi_bill_benefits

        form.subject.data = withdrawal_request.subject
        form.number.data = withdrawal_request.number
        form.section.data = withdrawal_request.section

        form.date.data = withdrawal_request.date

        form.initial.data = withdrawal_request.initial

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

            pdf_link = generate_withdrawal(data)

            # Pending or draft?
            if form.is_draft.data:
                status = "draft"
            else: status = "pending"

            # Update attribute values of request
            withdrawal_request.status = status
            withdrawal_request.pdf_link = pdf_link
            withdrawal_request.name = data['NAME']
            withdrawal_request.peoplesoft_id = data['PEOPLESOFT']
            withdrawal_request.college = data['COLLEGE']
            withdrawal_request.degree = data['DEGREE']
            withdrawal_request.city = data['CITY'],
            withdrawal_request.state = data['STATE']
            withdrawal_request.zip_code = data['ZIPCODE']
            withdrawal_request.phone = data['PHONE']
            withdrawal_request.email = data['EMAIL']
            withdrawal_request.term_year = data['TERMYEAR']
            withdrawal_request.last_attended = data['LASTATTENDED']
            withdrawal_request.reason = data['REASON']
            withdrawal_request.details = data['DETAILS']
            withdrawal_request.financial_assistance = data['FINANCIALASSISTANCE']
            withdrawal_request.uh_health_insurance = data['HEALTHINSURANCE']
            withdrawal_request.campus_housing = data['CAMPUSHOUSING']
            withdrawal_request.visa_status = data['VISASTATUS']
            withdrawal_request.gi_bill_benefits = data['GIBILL']
            withdrawal_request.subject = data['SUBJECT']
            withdrawal_request.number = data['NUMBER']
            withdrawal_request.section = data['SECTION']
            withdrawal_request.initial = data['INITIAL']
            withdrawal_request.date = form.date.data

            db.session.commit()

            return redirect(url_for('user.user_requests'))

    # Get current user and roles
    user = User.query.filter_by(azure_id=session['user']['sub']).first()
    roles = [role.name for role in user.roles]

    return render_template('medical_withdrawal.html', form=form, logged_in=True, roles=roles)