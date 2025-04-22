from app.models import Role, User, OrganizationalUnit, db

# Create default roles
def create_default_roles():
    roles = {
        'admin': 'Full administrative access',
        'user': 'Standard user access',
        'manager': 'Academic manager access',
        'employee': 'Employee access'
    }

    for role_name, description in roles.items():
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name, description=description)
            db.session.add(role)

    db.session.commit()

def create_organizational_units():
    root = OrganizationalUnit.query.filter_by(name='Academic and Student Services').first()
    if not root:
        root = OrganizationalUnit(name='Academic and Student Services')
        db.session.add(root)
        db.session.commit()
    
    # Check sub-units
    subunits = {
        'Identity and Records': None,
        'Advising': None,
        'Health and Wellness': None
    }

    for name in subunits:
        existing = OrganizationalUnit.query.filter_by(name=name, parent_id=root.id).first()
        if not existing:
            unit = OrganizationalUnit(name=name, parent_id=root.id)
            db.session.add(unit)

    db.session.commit()

def assign_manager_to_unit(unit_name, manager_id):
    # Fetch unit/manager
    unit = OrganizationalUnit.query.filter_by(name=unit_name).first()
    manager = User.query.get(manager_id)

    if unit and manager:
        unit.manager = manager
        db.session.commit()