from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
import os
from config.settings import Config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    app.config.from_object(config_class)
    
    # Initialize Flask extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    migrate.init_app(app, db)
    
    # Register blueprints
    from app.controllers.auth_controller import auth_bp
    from app.controllers.payment_controller import payment_bp
    from app.controllers.admin_controller import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(admin_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Import and register admin views
        from app.controllers.admin_controller import setup_admin
        setup_admin(app)
        
        # Initialize demo data if needed
        from app.utils.init_data import create_initial_data
        create_initial_data()
    
    return app