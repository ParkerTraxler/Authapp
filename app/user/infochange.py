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
            
            # Build FERPA request
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


# [TO DO] Edit a drafted/returned info change request