from flask_wtf import FlaskForm
from wtforms import DateField, StringField, SubmitField, BooleanField, SelectMultipleField, FileField
from wtforms.validators import DataRequired, Email, Length, Regexp

# Profile Form
class ProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    submit = SubmitField('Save Changes')

# User management form
class UserForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    active = BooleanField('Active', default=True)
    roles = SelectMultipleField('Roles', coerce=int)
    submit = SubmitField('Save Changes')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate roles from database
        from models import Role
        self.roles.choices = [(role.id, role.name) for role in Role.query.all()]

class FERPAForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=25)])
    campus = StringField('Campus', validators=[DataRequired(), Length(min=2, max=25)])
    
    # Checkboxes/other field for officials
    official_choices = SelectMultipleField("Select Officials", choices=[('registrar', 'Office of the University Registrar'),
        ('aid', 'Scholarships and Financial Aid'),
        ('financial', 'Student Financial Services'),
        ('undergrad', 'Undergraduate Scholars & US (formally USD)'),
        ('advancement', 'University Advancement'),
        ('dean', 'Dean of Students Office'),
        ('other', 'Other')], validators=[DataRequired()])

    official_other = StringField('Other Officials')

    # Checkboxes/other field for information type
    info_choices = SelectMultipleField("Select Info", choices=[('advising', 'Academic Advising Profile/Information'),
        ('all_records', 'All University Records'),
        ('academics', 'Academic Records'),
        ('billing', 'Billing/Financial Aid'),
        ('disciplinary', 'Disciplinary'),
        ('transcripts', 'Grades/Transcripts'),
        ('housing', 'Housing'),
        ('photos', 'Photos'),
        ('scholarship', 'Scholarship and/or Honors'),
        ('other', 'Other')], validators=[DataRequired()])

    info_other = StringField('Other Info')

    release_to = StringField('Release to', validators=[DataRequired(), Length(max=25)])
    purpose = StringField('Purpose', validators=[DataRequired(), Length(max=25)])

    additional_names = StringField('Additional Individuals', validators=[Length(max=25)])

    # Checkboxes/other field for who gets the info
    release_choices = SelectMultipleField('Select People', choices=[('family', 'Family'),
        ('institution', 'Educational Institution'),
        ('award', 'Honor or Award'),
        ('employer', 'Employer/Prospective Employer'),
        ('media', 'Public or Media of Scholarship'),
        ('other', 'Other')], validators=[DataRequired()])

    release_other = StringField('Other Releases')

    # Essential Info
    password = StringField('Password', validators=[DataRequired(), Length(min=5, max=16)])
    peoplesoft_id = StringField('PSID', validators=[DataRequired(), Length(min=6, max=6)])
    signature = FileField('Upload Signature', validators=[DataRequired()])
    date = DateField('Birthdate', format='%Y-%m-%d', validators=[DataRequired()])

    is_draft = BooleanField('Save as Draft?')

    submit = SubmitField('Submit FERPA')

class InfoChangeForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=25)])
    peoplesoft_id = StringField('UH ID', validators=[DataRequired(), Length(min=6, max=6)])

    # Choice for name/SSN
    choice = SelectMultipleField("Choose", choices=[('name', 'Update Name (Complete Section A)'),
        ('ssn', 'Update SSN (Complete Section B)')], validators=[DataRequired()])

    # Section A: Name Change
    first_name_old = StringField('Old Name', validators=[Length(max=25)])
    middle_name_old = StringField('Old Mid. Name', validators=[Length(max=25)])
    last_name_old = StringField('Old Last Name', validators=[Length(max=25)])
    suffix_old = StringField('Old Suffix', validators=[Length(max=10)])

    first_name_new = StringField('Old Name', validators=[Length(max=25)])
    middle_name_new = StringField('Old Mid. Name', validators=[Length(max=25)])
    last_name_new = StringField('Old Last Name', validators=[Length(max=25)])
    suffix_new = StringField('Old Suffix', validators=[Length(max=10)])

    # Reason for name change checkbox
    name_change_reason = SelectMultipleField("Reason for Name Change", choices=[('marriage', 'Marriage/Divorce'),
        ('court', 'Court Order'),
        ('error', 'Correction of Error')])

    # Section B: SSN Change
    ssn_old = StringField('Old SSN', validators=[Regexp(r"^$|^\d{3}-\d{2}-\d{4}$", message="SSN must be in the format XXX-XX-XXXX")])
    ssn_new = StringField('New SSN', validators=[Regexp(r"^$|^\d{3}-\d{2}-\d{4}$", message="SSN must be in the format XXX-XX-XXXX")])

    # Reason for SSN change checkbox
    ssn_change_reason = SelectMultipleField("Reason for SSN Change", choices=[('error', 'Correction of Error'),
        ('addition', 'Addition of SSN to University Records')])

    # Signature and date
    signature = FileField('Upload Signature', validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])

    submit = SubmitField('Submit SSN/Name Change')
