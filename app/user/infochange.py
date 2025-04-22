import os, uuid
from datetime import datetime
from flask import request, session, render_template, flash, redirect, url_for, current_app
from app.models import User, Request, RequestType, OrganizationalUnit, db
from app.auth.role_required import role_required
from app.forms import InfoChangeForm
from app.utils.request_utils import allowed_file, return_choice, generate_ssn_name
from app.user import user_bp

@user_bp.route('/requests/info_change', methods=['GET', 'POST'])
@role_required('user')
def info_change_request():

    # Name/SSN change form
    form = InfoChangeForm()

    # Get current user from session
    user = User.query.filter_by(azure_id=session['user']['sub']).first()

    if not form.validate_on_submit():
        print(form.errors)

    if form.validate_on_submit():
        # Ensure the user uploaded a signature
        if 'signature' not in request.files:
            flash('Signature was not uploaded.', 'danger')
            return render_template('info_change.html', form=form, logged_in=True)

        file = request.files['signature']
        if file.filename == '':
            flash('No file selected for signature.', 'danger')
            return render_template('info_change.html', form=form, logged_in=True)

        # Check the file is allowed
        if file and allowed_file(file.filename):
            
            # Generate a unique name for the image
            unique_filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()

            # Save file with new name
            filepath = os.path.normpath(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
            file.save(filepath)

            latex_path = filepath.replace("\\", "/")

            # Get user id from session
            user_id = user.id
            
            # Construct dictionary for the PDF
            choice = form.choice.data
            name_change_reason = form.name_change_reason.data
            ssn_change_reason = form.ssn_change_reason.data

            data = {
                "NAME": form.name.data, 
                "PEOPLESOFT": form.peoplesoft_id.data,
                "EDIT_NAME": return_choice(choice, 'name'),
                "EDIT_SSN": return_choice(choice, 'ssn'),
                "FN_OLD": form.first_name_old.data, "MN_OLD": form.middle_name_old.data, "LN_OLD": form.last_name_old.data, "SUF_OLD": form.suffix_old.data,
                "FN_NEW": form.first_name_new.data, "MN_NEW": form.middle_name_new.data, "LN_NEW": form.last_name_new.data, "SUF_NEW": form.suffix_new.data,
                "OPT_MARITAL": return_choice(name_change_reason, 'marriage'),
                "OPT_COURT": return_choice(name_change_reason, 'court'),
                "OPT_ERROR_NAME": return_choice(name_change_reason, 'error'),
                "SSN_OLD": form.ssn_old.data, "SSN_NEW": form.ssn_new.data,
                "OPT_ERROR_SSN": return_choice(ssn_change_reason, 'error'),
                "OPT_ADD_SSN": return_choice(ssn_change_reason, 'addition'),
                "SIGNATURE": latex_path,
                "DATE": str(form.date.data)}

            # Pass dictionary to function
            pdf_link = generate_ssn_name(data)

            if form.is_draft.data: status = "draft"
            else: status = "pending"

            # Get organizational unit for form, make sure it and the manager exist
            infochange_unit = OrganizationalUnit.query.filter_by(name='Identity and Records').first()
            if not infochange_unit or not infochange_unit.manager_id:
                flash('Information change request cannot be submitted. No manager found for Identity and Records.', 'error')
                return redirect(url_for('user.user_requests'))
            
            # Build information change request
            new_request = Request(
                user_id=user_id,
                status=status,
                request_type=RequestType.INFO,
                pdf_link=pdf_link,
                sig_link=unique_filename,
                form_data=data,
                current_approver_id=infochange_unit.manager_id,
                current_unit_id=infochange_unit.id
            )

            # Commit infochange request to database
            db.session.add(new_request)
            db.session.commit()
            
            return redirect(url_for('user.user_requests'))

    # Get current user and roles
    roles = [role.name for role in user.roles]

    return render_template('info_change.html', form=form, logged_in=True, roles=roles)


# Edit a drafted/returned info change request
@user_bp.route('/requests/edit-infochange-request/<infochange_request_id>', methods=['GET', 'POST'])
@role_required('user')
def edit_infochange_request(infochange_request_id):
    # Ensure the user is logged in, get roles
    if not session.get('logged_in', False):
        return redirect(url_for("auth.login"))
    
    # Ensure the request exists
    infochange_request = Request.query.get_or_404(infochange_request_id)
    if not infochange_request:
        flash('FERPA request was not found.', 'error')
        return redirect(url_for("user.user_requests"))
    
    if infochange_request.status == "pending":
        flash('Information change request was already submitted. No further modifications are allowed until approved by a manager.')
        return redirect(url_for("user.user_requests"))
    elif infochange_request.status == "approved":
        flash('Information change request was already approved. No further modifications are allowed.')
        return redirect(url_for("user.user_requests"))
    elif infochange_request.status == "rejected":
        flash('Information change request was rejected. No further modifications are allowed.')
        return redirect(url_for("user.user_requests"))
    
    # Create form, populate with user data
    form = InfoChangeForm()

    # Populate non-choice fields from database
    data = infochange_request.form_data

    options = {'EDIT_NAME': 'name', 'EDIT_SSN': 'ssn'}
    choices = [value for opt, value in options.items()
               if data.get(opt) == "yes"]
    
    nmchg_options = {'OPT_MARITAL': 'marriage',
                     'OPT_COURT': 'court',
                     'OPT_ERROR_NAME': 'error'}
    nmchg_choices = [value for opt, value in options.items()
                     if data.get(opt) == "yes"]
    
    ssnchg_options = {'OPT_ERROR_SSN': 'error', 'OPT_ADD_SSN': 'addition'}
    ssnchg_choices = [value for opt, value in ssnchg_options.items()
                      if data.get(opt) == "yes"]

    if request.method == 'GET':
        form.name.data = data['NAME']
        form.peoplesoft_id.data = data['PEOPLESOFT']

        form.choice.data = infochange_request.choice.split(',')

        form.first_name_old.data = data['FN_OLD']
        form.middle_name_old.data = data['MN_OLD']
        form.last_name_old.data = data['LN_OLD']
        form.suffix_old.data = data['SUF_OLD']

        form.first_name_new.data = data['FN_NEW']
        form.middle_name_new.data = data['MN_NEW']
        form.last_name_new.data = data['LN_NEW']
        form.suffix_new.data = data['SUF_NEW']

        form.name_change_reason.data = nmchg_choices

        form.ssn_old.data = data['SSN_OLD']
        form.ssn_new.data = data['SSN_NEW']

        form.ssn_change_reason.data = ssnchg_choices

        form.date.data = form.date.data = datetime.strptime(data['DATE'], '%Y-%m-%d').date()

    if form.validate_on_submit():
        
        # Ensure the user uploaded a signature
        if 'signature' not in request.files:
            flash('Signature was not uploaded.', 'danger')
            return render_template('ferpa.html', form=form, logged_in=True)
        
        file = request.files['signature']
        if file.filename == '':
            flash('No file selected for signature.', 'danger')
            return render_template('ferpa.html', form=form, logged_in=True)
        
        # Check the file is allowed
        if file and allowed_file(file.filename):
        # Generate a unique name for the image
            unique_filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()

            # Save file with new name
            filepath = os.path.normpath(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
            file.save(filepath)

            latex_path = filepath.replace("\\", "/")

            # Construct dictionary for the PDF
            choice = form.choice.data
            name_change_reason = form.name_change_reason.data
            ssn_change_reason = form.ssn_change_reason.data

            new_data = {
                "NAME": form.name.data, 
                "PEOPLESOFT": form.peoplesoft_id.data,
                "EDIT_NAME": return_choice(choice, 'name'),
                "EDIT_SSN": return_choice(choice, 'ssn'),
                "FN_OLD": form.first_name_old.data, "MN_OLD": form.middle_name_old.data, "LN_OLD": form.last_name_old.data, "SUF_OLD": form.suffix_old.data,
                "FN_NEW": form.first_name_new.data, "MN_NEW": form.middle_name_new.data, "LN_NEW": form.last_name_new.data, "SUF_NEW": form.suffix_new.data,
                "OPT_MARITAL": return_choice(name_change_reason, 'marriage'),
                "OPT_COURT": return_choice(name_change_reason, 'court'),
                "OPT_ERROR_NAME": return_choice(name_change_reason, 'error'),
                "SSN_OLD": form.ssn_old.data, "SSN_NEW": form.ssn_new.data,
                "OPT_ERROR_SSN": return_choice(ssn_change_reason, 'error'),
                "OPT_ADD_SSN": return_choice(ssn_change_reason, 'addition'),
                "SIGNATURE": latex_path,
                "DATE": str(form.date.data)}
            
            # Generate PDF and store path
            pdf_link = generate_ssn_name(new_data)

            if form.is_draft.data: status = "draft"
            else: status = "pending"

            # Update fields of request
            infochange_request.status = status
            infochange_request.pdf_link = pdf_link
            infochange_request.form_data = new_data

            db.session.commit()

            return redirect(url_for('user.user_requests'))
        
    user = User.query.filter_by(azure_id=session['user']['sub']).first()
    roles = [role.name for role in user.roles]

    return render_template('info_change.html', form=form, logged_in=True, roles=roles)