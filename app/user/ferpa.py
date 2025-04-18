import os, uuid
from flask import request, session, render_template, flash, redirect, url_for, current_app
from app.models import User, Request, RequestType, db
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

            if form.is_draft.data: status = "draft"
            else: status = "pending"
            
            # Create new FERPA request
            new_request = Request(
                user_id=user.id,
                status=status,
                request_type=RequestType.FERPA,
                pdf_link=pdf_file,
                sig_link=unique_filename,
                form_data=data
            )

            # Commit FERPA request to database
            db.session.add(new_request)
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
    
    # Ensure the request exists
    ferpa_request = Request.query.get_or_404(ferpa_request_id)
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
    
    # Parse form data from request, populate fields in draft form
    data = ferpa_request.form_data

    official_options = {'OPT_REGISTRAR': 'registrar',
                         'OPT_AID': 'aid', 
                         'OPT_FINANCIAL': 'financial', 
                         'OPT_UNDERGRAD': 'undergrad', 
                         'OPT_ADVANCEMENT': 'advancement', 
                         'OPT_DEAN': 'dean', 
                         'OPT_OTHER_OFFICIALS': 'other'}
    
    official_choices = [value for opt, value in official_options.items()
                        if data.get(opt) == "yes"]
    
    info_options = {'OPT_ACADEMIC_INFO': 'advising',
                    'OPT_UNIVERSITY_RECORDS': 'all_records',
                    'OPT_ACADEMIC_RECORDS': 'academics',
                    'OPT_BILLING': 'billing',
                    'OPT_DISCIPLINARY': 'disciplinary',
                    'OPT_TRANSCRIPTS': 'transcripts',
                    'OPT_HOUSING': 'housing',
                    'OPT_PHOTOS': 'photos',
                    'OPT_SCHOLARSHIP': 'scholarship',
                    'OPT_OTHER_INFO': 'other'}
    
    info_choices = [value for opt, value in info_options.items()
                    if data.get(opt) == "yes"]
    
    release_options = {'OPT_FAMILY': 'family',
                       'OPT_INSTITUTION': 'institution',
                       'OPT_HONOR': 'award',
                       'OPT_EMPLOYER': 'employer',
                       'OPT_PUBLIC': 'media',
                       'OPT_OTHER_RELEASE': 'other'}
    
    release_choices = [value for opt, value in release_options.items()
                       if data.get(opt) == "yes"]

    if request.method == 'GET':
        form.name.data = data['NAME']
        form.campus.data = data['CAMPUS']

        form.official_choices.data = official_choices
        form.official_other.data = data['OTHEROFFICIALS']

        form.info_choices.data = info_choices
        form.info_other.data = data['OTHERINFO']

        form.release_choices.data = release_choices
        form.release_other.data = data['OTHERRELEASE']

        form.release_to.data = data['RELEASE']
        form.purpose.data = data['PURPOSE']
        form.additional_names.data = data['ADDITIONALS']

        form.password.data = data['PASSWORD']
        form.peoplesoft_id.data = data['PEOPLESOFT']
        form.date.data = data['DATE']

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

            new_data = {
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
            pdf_link = generate_ferpa(new_data)

            # Pending or draft?
            if form.is_draft.data: status = "draft"
            else: status = "pending"
            
            # Update attributes of request
            ferpa_request.status = status
            ferpa_request.pdf_link = pdf_link
            ferpa_request.form_data = new_data

            # Commit FERPA request to database
            db.session.commit()

            return redirect(url_for('user.user_requests'))
    
    # Get current user and roles
    user = User.query.filter_by(azure_id=session['user']['sub']).first()
    roles = [role.name for role in user.roles]

    return render_template('ferpa.html', form=form, logged_in=True, roles=roles)