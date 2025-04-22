from flask import Blueprint

employee_bp = Blueprint('employee', __name__)

from . import routes