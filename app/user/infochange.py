import os, uuid
from flask import request, session, render_template, flash, redirect, url_for, current_app
from app.models import User, InfoChangeRequest, db
from app.auth.role_required import role_required
from app.forms import InfoChangeForm
from app.utils.request_utils import allowed_file, return_choice, generate_ssn_name
from app.user import user_bp

@user_bp.route('/requests/info_change', methods=['GET', 'POST'])
@role_required('user')
def info_change_request():

    # Name/SSN change form
    form = InfoChangeForm()

    # Get current user
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
            user = User.query.filter_by(azure_id=session['user']['sub']).first()
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
            
            # Build information change request
            new_info_request = InfoChangeRequest(
                user_id=user_id,
                status="pending",
                pdf_link=pdf_link,
                name=data['NAME'],
                peoplesoft_id=data['PEOPLESOFT'],
                choice="blank",
                fname_old=data['FN_OLD'],
                mname_old=data['MN_OLD'],
                lname_old=data['LN_OLD'],
                sfx_old=data['SUF_OLD'],
                fname_new=data['FN_NEW'],
                mname_new=data['MN_NEW'],
                lname_new=data['LN_NEW'],
                sfx_new=data['SUF_NEW'],
                nmchg_reason="blank",
                ssn_old=data['SSN_OLD'],
                ssn_new=data['SSN_NEW'],
                ssnchg_reason="blank",
                date=data['DATE']
            )

            # Commit infochange request to database
            db.session.add(new_info_request)
            db.session.commit()
            
            return redirect(url_for('user.user_requests'))

    # Get current user and roles
    user = User.query.filter_by(azure_id=session['user']['sub']).first()
    roles = [role.name for role in user.roles]

    return render_template('info_change.html', form=form, logged_in=True, roles=roles)


# Edit a drafted/returned info change request
@user_bp.route('/requests/edit-infochange-request/<infochange_request_id>', methods=['GET', 'POST'])
@role_required('user')
def edit_infochange_request(infochange_request_id):
    # Ensure the user is logged in, get roles
    if not session.get('logged_in', False):
        return redirect(url_for("auth.login"))
    
    print('Logged in')
    
    # Ensure the request exists
    infochange_request = InfoChangeRequest.query.get_or_404(infochange_request_id)
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
    
    print('Request exists')
    
    # Create form, populate with user data
    form = InfoChangeForm()

    # Populate non-choice fields from database
    if request.method == 'GET':
        print('Getting variables')
        form.name.data = infochange_request.name
        form.peoplesoft_id.data = infochange_request.peoplesoft_id

        form.choice.data = infochange_request.choice.split(',')

        form.first_name_old.data = infochange_request.fname_old
        form.middle_name_old.data = infochange_request.mname_old
        form.last_name_old.data = infochange_request.lname_old
        form.suffix_old.data = infochange_request.sfx_old

        form.first_name_new.data = infochange_request.fname_new
        form.middle_name_new.data = infochange_request.mname_new
        form.last_name_new.data = infochange_request.lname_new
        form.suffix_new.data = infochange_request.sfx_new

        form.name_change_reason.data = infochange_request.nmchg_reason.split(',')

        form.ssn_old.data = infochange_request.ssn_old
        form.ssn_new.data = infochange_request.ssn_new

        form.ssn_change_reason.data = infochange_request.ssnchg_reason.split(',')

        form.date.data = infochange_request.date

        print('Successfully printed form variables')

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
            
            # Generate PDF and store path
            pdf_file = generate_ssn_name(data)

            # Store choices as comma-separated strings
            choice = ",".join(form.choice.data)
            name_change_reason = ",".join(form.name_change_reason.data)
            ssn_change_reason = ",".join(form.ssn_change_reason.data)

            if form.is_draft.data:
                status = "draft"
            else:
                status = "pending"

            # Update fields of request
            infochange_request.status = status
            infochange_request.pdf_link = pdf_file
            infochange_request.name = data['NAME']
            infochange_request.peoplesoft_id = data['PEOPLESOFT']
            infochange_request.choice = choice
            infochange_request.fname_old = data['FN_OLD']
            infochange_request.mname_old = data['MN_OLD']
            infochange_request.lname_old = data['LN_OLD']
            infochange_request.sfx_old = data['SUF_OLD']
            infochange_request.fname_new = data['FN_NEW']
            infochange_request.mname_new = data['MN_NEW']
            infochange_request.lname_new = data['LN_NEW']
            infochange_request.sfx_new = data['SUF_NEW']
            infochange_request.nmchg_reason = name_change_reason
            infochange_request.ssn_old = data['SSN_OLD']
            infochange_request.ssn_new = data['SSN_NEW']
            infochange_request.ssnchg_reason = ssn_change_reason
            infochange_request.date = form.date.data

            db.session.commit()

            return redirect(url_for('user.user_requests'))
        
    user = User.query.filter_by(azure_id=session['user']['sub']).first()
    roles = [role.name for role in user.roles]

    return render_template('info_change.html', form=form, logged_in=True, roles=roles)