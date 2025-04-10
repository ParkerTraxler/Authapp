import os, uuid
from flask import request, session, render_template, flash, redirect, url_for, current_app
from app.models import User, FERPARequest, db
from app.auth.role_required import role_required
from app.forms import FERPAForm
from app.user import user_bp
from app.utils.request_utils import allowed_file, return_choice, generate_ferpa

# Create a new FERPA request via a form
@user_bp.route('/requests/ferpa', methods=['GET', 'POST'])
@role_required('user')
def ferpa_request():
    # User FERPA form
    form = FERPAForm()

    # Get current user
    user = User.query.filter_by(azure_id=session['user']['sub']).first()

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

            # Get user id from session
            user_id = user.id

            # Construct a dictionary for the PDF
            official_choices = form.official_choices.data
            info_choices = form.info_choices.data
            release_choices = form.release_choices.data

            data = {
                 "NAME": form.name.data, "CAMPUS": form.campus.data,
                 
                 "OPT_REGISTRAR": return_choice(official_choices, 'registrar'),
                 "OPT_AID": return_choice(official_choices, 'aid'),
                 "OPT_FINANCIAL": return_choice(official_choices, 'financial'),
                 "OPT_UNDERGRAD": return_choice(official_choices, 'undergrad'),
                 "OPT_ADVANCEMENT": return_choice(official_choices, 'advancement'),
                 "OPT_DEAN": return_choice(official_choices, 'dean'),
                 "OPT_OTHER_OFFICIALS": return_choice(official_choices, 'other'),
                 "OTHEROFFICIALS": form.official_other.data,

                 "OPT_ACADEMIC_INFO": return_choice(info_choices, 'advising'),
                 "OPT_UNIVERSITY_RECORDS": return_choice(info_choices, 'all_records'),
                 "OPT_ACADEMIC_RECORDS": return_choice(info_choices, 'academics'),
                 "OPT_BILLING": return_choice(info_choices, 'billing'),
                 "OPT_DISCIPLINARY": return_choice(info_choices, 'disciplinary'),
                 "OPT_TRANSCRIPTS": return_choice(info_choices, 'transcripts'),
                 "OPT_HOUSING": return_choice(info_choices, 'housing'),
                 "OPT_PHOTOS": return_choice(info_choices, 'photos'),
                 "OPT_SCHOLARSHIP": return_choice(info_choices, 'scholarship'),
                 "OPT_OTHER_INFO": return_choice(info_choices, 'other'),
                 "OTHERINFO": form.info_other.data,

                 "RELEASE": form.release_to.data, "PURPOSE": form.purpose.data, "ADDITIONALS": form.additional_names.data,

                 "OPT_FAMILY": return_choice(release_choices, 'family'),
                 "OPT_INSTITUTION": return_choice(release_choices, 'institution'),
                 "OPT_HONOR": return_choice(release_choices, 'award'),
                 "OPT_EMPLOYER": return_choice(release_choices, 'employer'),
                 "OPT_PUBLIC": return_choice(release_choices, 'media'),
                 "OPT_OTHER_RELEASE": return_choice(release_choices, 'other'),
                 "OTHERRELEASE": form.release_other.data,

                 "PASSWORD": form.password.data, "PEOPLESOFT": form.peoplesoft_id.data, "SIGNATURE": latex_path, "DATE": str(form.date.data)
            }

            # Generate PDF and store path
            pdf_file = generate_ferpa(data)

            # Store options as comma-separate string
            official_choices = ",".join(form.official_choices.data)
            info_choices = ",".join(form.info_choices.data)
            release_choices = ",".join(form.release_choices.data)

            if form.is_draft.data:
                status = "draft"
            else:
                status = "pending"
            
            # Create new FERPA request
            new_ferpa_request = FERPARequest(
                user_id=user_id,
                status=status,
                pdf_link=pdf_file,
                sig_link=unique_filename,
                name=data['NAME'],
                campus=data['CAMPUS'],
                official_choices=official_choices,
                official_other=data['OTHEROFFICIALS'],
                info_choices=info_choices,
                info_other=data['OTHERINFO'],
                release_choices=release_choices,
                release_other=data['OTHERRELEASE'],
                release_to=data['RELEASE'],
                purpose=data['PURPOSE'],
                additional_names=data['ADDITIONALS'],
                password=data['PASSWORD'],
                peoplesoft_id=data['PEOPLESOFT'],
                date=data['DATE']
            )

            # Commit FERPA request to database
            db.session.add(new_ferpa_request)
            db.session.commit()

            return redirect(url_for('user.user_requests'))

    # Get current user and roles
    user = User.query.filter_by(azure_id=session['user']['sub']).first()
    roles = [role.name for role in user.roles]

    return render_template('ferpa.html', form=form, logged_in=True, roles=roles)

# Edit drafted/returned FERPA form
@user_bp.route('/requests/edit-ferpa-request/<ferpa_request_id>', methods=['GET', 'POST'])
@role_required('user')
def edit_ferpa_request(ferpa_request_id):
    # Ensure the user is logged in, get roles
    if not session.get('logged_in', False):
        return redirect(url_for("auth.login"))
    
    # Ensure the user exists
    ferpa_request = FERPARequest.query.get_or_404(ferpa_request_id)
    if not ferpa_request:
        flash('FERPA request was not found.', 'error')
        return redirect(url_for("user.user_requests"))
    
    if ferpa_request.status == "pending":
        flash('FERPA request was already submitted. No further modifications are permitted until approved by a manager.')
        return redirect(url_for("user.user_requests"))
    elif ferpa_request.status == "approved":
        flash('FERPA request was already approved. No further modifications are allowed.')
        return redirect(url_for("user.user_requests"))
    elif ferpa_request.status == "rejected":
        flash('FERPA request was rejected. No further modifications are allowed.')
        return redirect(url_for("user.user_requests"))

    # Create form, populate with user data
    form = FERPAForm()

    # Populate non-choice fields from database
    if request.method == 'GET':
        form.name.data = ferpa_request.name
        form.campus.data = ferpa_request.campus

        form.official_choices.data = ferpa_request.official_choices.split(',')
        form.official_other.data = ferpa_request.official_other

        form.info_choices.data = ferpa_request.info_choices.split(',')
        form.info_other.data = ferpa_request.info_other

        form.release_choices.data = ferpa_request.release_choices.split(',')
        form.release_other.data = ferpa_request.release_other

        form.release_to.data = ferpa_request.release_to
        form.purpose.data = ferpa_request.purpose
        form.additional_names.data = ferpa_request.additional_names

        form.password.data = ferpa_request.password
        form.peoplesoft_id.data = ferpa_request.peoplesoft_id
        form.date.data = ferpa_request.date

    # Handle form submission
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

            # Construct a dictionary for the PDF
            official_choices = form.official_choices.data
            info_choices = form.info_choices.data
            release_choices = form.release_choices.data

            data = {
                 "NAME": form.name.data, "CAMPUS": form.campus.data,
                 
                 "OPT_REGISTRAR": return_choice(official_choices, 'registrar'),
                 "OPT_AID": return_choice(official_choices, 'aid'),
                 "OPT_FINANCIAL": return_choice(official_choices, 'financial'),
                 "OPT_UNDERGRAD": return_choice(official_choices, 'undergrad'),
                 "OPT_ADVANCEMENT": return_choice(official_choices, 'advancement'),
                 "OPT_DEAN": return_choice(official_choices, 'dean'),
                 "OPT_OTHER_OFFICIALS": return_choice(official_choices, 'other'),
                 "OTHEROFFICIALS": form.official_other.data,

                 "OPT_ACADEMIC_INFO": return_choice(info_choices, 'advising'),
                 "OPT_UNIVERSITY_RECORDS": return_choice(info_choices, 'all_records'),
                 "OPT_ACADEMIC_RECORDS": return_choice(info_choices, 'academics'),
                 "OPT_BILLING": return_choice(info_choices, 'billing'),
                 "OPT_DISCIPLINARY": return_choice(info_choices, 'disciplinary'),
                 "OPT_TRANSCRIPTS": return_choice(info_choices, 'transcripts'),
                 "OPT_HOUSING": return_choice(info_choices, 'housing'),
                 "OPT_PHOTOS": return_choice(info_choices, 'photos'),
                 "OPT_SCHOLARSHIP": return_choice(info_choices, 'scholarship'),
                 "OPT_OTHER_INFO": return_choice(info_choices, 'other'),
                 "OTHERINFO": form.info_other.data,

                 "RELEASE": form.release_to.data, "PURPOSE": form.purpose.data, "ADDITIONALS": form.additional_names.data,

                 "OPT_FAMILY": return_choice(release_choices, 'family'),
                 "OPT_INSTITUTION": return_choice(release_choices, 'institution'),
                 "OPT_HONOR": return_choice(release_choices, 'award'),
                 "OPT_EMPLOYER": return_choice(release_choices, 'employer'),
                 "OPT_PUBLIC": return_choice(release_choices, 'media'),
                 "OPT_OTHER_RELEASE": return_choice(release_choices, 'other'),
                 "OTHERRELEASE": form.release_other.data,

                 "PASSWORD": form.password.data, "PEOPLESOFT": form.peoplesoft_id.data, "SIGNATURE": latex_path, "DATE": str(form.date.data)
            }

            # Generate PDF and store path
            pdf_file = generate_ferpa(data)

            # Store options as comma-separate string
            official_choices = ",".join(form.official_choices.data)
            info_choices = ",".join(form.info_choices.data)
            release_choices = ",".join(form.release_choices.data)

            if form.is_draft.data:
                status = "draft"
            else:
                status = "pending"
            
            # Update attributes of request
            ferpa_request.status = status
            ferpa_request.pdf_link = pdf_file,
            ferpa_request.name = data['NAME']
            ferpa_request.campus = data['CAMPUS']
            ferpa_request.official_choices = official_choices
            ferpa_request.official_other = data['OTHEROFFICIALS']
            ferpa_request.info_choices = info_choices
            ferpa_request.info_other = data['OTHERINFO']
            ferpa_request.release_choices = release_choices
            ferpa_request.release_other = data['OTHERRELEASE']
            ferpa_request.release_to = data['RELEASE']
            ferpa_request.purpose = data['PURPOSE']
            ferpa_request.additional_names = data['ADDITIONALS']
            ferpa_request.password = data['PASSWORD']
            ferpa_request.peoplesoft_id = data['PEOPLESOFT']
            ferpa_request.date = form.date.data

            # Commit FERPA request to database
            db.session.commit()

            return redirect(url_for('user.user_requests'))
    
    # Get current user and roles
    user = User.query.filter_by(azure_id=session['user']['sub']).first()
    roles = [role.name for role in user.roles]

    return render_template('ferpa.html', form=form, logged_in=True, roles=roles)