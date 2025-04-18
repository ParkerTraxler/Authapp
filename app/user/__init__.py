from flask import Blueprint

user_bp = Blueprint('user', __name__)

from . import dashboard, edit_router, ferpa, infochange, medicalwithdrawal, studentdrop