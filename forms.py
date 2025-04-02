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
    
    # Authorized checkpoints AND optional 'other' field

    # Categories checkpoints AND optional 'other' field

    release_to = StringField('Release to', validators=[DataRequired(), Length(max=25)])
    purpose = StringField('Purpose', validators=[DataRequired(), Length(max=25)])

    additional_names = StringField('Additional Individuals', validators=[DataRequired(), Length(max=25)])

    # Individuals checkpoints AND optional 'other' field

    password = StringField('Password', validators=[DataRequired(), Length(min=5, max=16)])

    peoplesoft_id = StringField('PSID', validators=[DataRequired(), Length(min=6, max=6)])
    signature = FileField('Upload Signature', validators=[DataRequired()])
    date = DateField('Birthdate', format='%Y-%m-%d', validators=[DataRequired()])

    submit = SubmitField('Submit FERPA')


class InfoChangeForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=25)])
    peoplesoft_id = StringField('UH ID', validators=[DataRequired(), Length(min=6, max=6)])

    # Choice for name/SSN

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

    # Section B: SSN Change
    ssn_old = StringField('Old SSN', validators=[Regexp(r"^\d{3}-\d{2}-\d{4}$", message="SSN must be in the format XXX-XX-XXXX")])
    ssn_new = StringField('New SSN', validators=[Regexp(r"^\d{3}-\d{2}-\d{4}$", message="SSN must be in the format XXX-XX-XXXX")])

    # Reason for SSN change checkbox

    # Signature and date
    signature = FileField('Upload Signature', validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])

    submit = SubmitField('Submit SSN/Name Change')
