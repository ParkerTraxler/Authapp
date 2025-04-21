from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.utils.db_utils import create_default_roles, create_organizational_units
from app.utils.file_utils import create_upload_folders
from .models import db
from .config import Config
from dotenv import load_dotenv

def create_app(config=Config):
    app = Flask(__name__)

    # Load config
    app.config.from_object(config)

    # Initialize database with app
    db.init_app(app)
    migrate = Migrate(app, db)

    # Register blueprints
    from app.auth import auth_bp
    from app.main import main_bp
    from app.user import user_bp
    from app.admin import admin_bp
    from app.manager import manager_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(manager_bp, url_prefix='/manager')

    # Create tables and default roles
    with app.app_context():
        db.create_all()
        create_default_roles()
        create_organizational_units()

    # Create upload folders for forms/signatures
    create_upload_folders(app.config['FORM_FOLDER'], app.config['UPLOAD_FOLDER'])

    return app