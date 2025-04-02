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
    signature = db.Column(db.String(100), nullable=True)

    user = db.relationship('User', back_populates='requests')
