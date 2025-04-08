from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Association table for users and roles
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True))

# Role model
class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __repr__(self):
        return f"<Role {self.name}>"

# User model
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    azure_id = db.Column(db.String(100), unique=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    roles = db.relationship('Role', secondary=user_roles, backref=db.backref('users', lazy='dynamic'))
    active = db.Column(db.Boolean(), default=True)

    requests = db.relationship('Request', back_populates='user', lazy=True)

    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)

    def __repr__(self):
        return f"<User {self.name}>"

# Requests model
class Request (db.Model):
    __tablename__ = 'requests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(10), nullable=False)
    req_type = db.Column(db.String(15), nullable=False)
    time = db.Column(db.DateTime, server_default=db.func.now())
    pdf_link = db.Column(db.String(100), nullable=True)

    user = db.relationship('User', back_populates='requests')

class FERPARequest(db.Model):
    __tablename__ = 'ferpa_requests'

    id = db.Column(db.Integer, primary_key=True)
    
    # Meta data
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(10), nullable=False)
    time = db.Column(db.DateTime, server_default=db.func.now())
    pdf_link = db.Column(db.String(100), nullable=False)

    # Officials
    official_choices = db.Column(db.String(25)) # comma-separated string
    official_other = db.Column(db.String(25))

    # Information
    info_choices = db.Column(db.String(25)) # comma-separated string
    info_other = db.Column(db.String(25))

    # Release
    release_choices = db.Column(db.String(25)) # comma-separated string
    release_other = db.Column(db.String(25))

    # essential info
    password = db.Column(db.String(25), nullable=False)
    peoplesoft_id = db.Column(db.String(25), nullable=False)
    date = db.Column(db.Date(), nullable=False)

class InfoChangeRequest(db.Model):
    __tablename__ = 'infochange_requests'

    id = db.Column(db.Integer, primary_key=True)

    # Meta data
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(10), nullable=False)
    time = db.Column(db.DateTime, server_default=db.func.now())
    pdf_link = db.Column(db.String(100), nullable=False)

    # Name and ID
    name = db.Column(db.String(25), nullable=False)
    peoplesoft_id = db.Column(db.String(6), nullable=False)

    # Choice for Name/SSN
    choice = db.Column(db.String(25), nullable=False)

    # Section A: Name Change
    fname_old = db.Column(db.String(25))
    mname_old = db.Column(db.String(25))
    lname_old = db.Column(db.String(25))
    sfx_old = db.Column(db.String(25))

    fname_new = db.Column(db.String(25))
    mname_new = db.Column(db.String(25))
    lname_new = db.Column(db.String(25))
    sfx_new = db.Column(db.String(25))

    # Reason for name change
    nmchg_reason = db.Column(db.String(25))

    # Section B: SSN Change
    ssn_new = db.Column(db.String(11))
    ssn_old = db.Column(db.String(11))

    # Reason for SSN change
    ssnchg_reason = db.Column(db.String(25))

    # Signature/Date
    date = db.Column(db.Date(), nullable=False)