from app.models import Role, User, OrganizationalUnit, RequestStep, RequestType, db
from flask import flash

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

def create_approval_steps(request_type, org_units):
    for i, org_unit in enumerate(org_units, start=1):
        step = RequestStep(
            request_type=request_type,
            step_number=i,
            org_unit_id=org_unit.id
        )
        db.session.add(step)
    
    db.session.commit()
    print(f"Base approval steps created for {request_type.name}.")

def get_units_in_order(names):
    # Gets list of organizational units as a set from the database, sorts them via a map
    units = OrganizationalUnit.query.filter(OrganizationalUnit.name.in_(names)).all()

    unit_map = {unit.name: unit for unit in units}
    return [unit_map[name] for name in names if name in unit_map]

def create_approval_steps_all():
    # Define organizational units for each request type
    ferpa_units = get_units_in_order(['Identity and Records', 'Academic and Student Services'])
    infochange_units = get_units_in_order(['Identity and Records', 'Academic and Student Services'])
    medical_units = get_units_in_order(['Health and Wellness', 'Academic and Student Services'])
    drop_units = get_units_in_order(['Advising', 'Academic and Student Services'])

    # Create base approval steps for each request type
    create_approval_steps(RequestType.FERPA, ferpa_units)
    create_approval_steps(RequestType.INFO, infochange_units)
    create_approval_steps(RequestType.MEDICAL, medical_units)
    create_approval_steps(RequestType.DROP, drop_units)

def assign_manager_to_unit(unit_name, manager_id):
    # Fetch unit/manager
    unit = OrganizationalUnit.query.filter_by(name=unit_name).first()
    manager = User.query.get(manager_id)

    if unit and manager:
        unit.manager = manager
        db.session.commit()

def advance_request(request):
    # Get steps for the request type
    steps = (
        RequestStep.query
        .filter_by(request_type=request.request_type)
        .order_by(RequestStep.step_number)
        .all()
    )

    # Get current step
    current_step = request.current_step_number or 0

    # Get next step
    next_step = next((step for step in steps if step.step_number == current_step + 1), None)

    # There is a next step (go to next step)
    if next_step:
        # Set next step number
        request.current_step_number = next_step.step_number

        # Set current_unit_id and current_approver_id (manager of that new unit)
        request.current_unit_id = next_step.org_unit_id
        request.current_approver_id = next_step.org_unit.manager_id

        # Set delegated status
        request.delegated_to_id = None

        db.session.commit()
        flash(f'The request has been forwarded to {next_step.org_unit.name} for further approval.', 'info')

    # There is not a next step and there is a parent (go to the parent)
    elif not next_step and request.current_unit.parent:
        # Advance request to parent
        parent_unit = request.current_unit.parent
        request.current_unit_id = parent_unit.id
        request.current_approver_id = parent_unit.manager_id

        request.delegated_to_id = None
        request.modified_at = db.func.now()

        db.session.commit()
        flash(f'The request has been forwarded to {parent_unit.name} for further approval.', 'info')
    # All steps and necessary approvals completed (final approval)
    else:
        request.status = 'approved'
        request.current_approver_id = None
        request.modified_at = db.func.now()

        flash(f'The request has been approved successfully.', 'success')
        db.session.commit()