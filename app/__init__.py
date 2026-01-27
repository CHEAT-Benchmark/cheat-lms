from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from app.config import Config, DATA_DIR

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.courses import courses_bp
    from app.routes.assignments import assignments_bp
    from app.routes.submissions import submissions_bp
    from app.routes.telemetry_api import telemetry_api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(assignments_bp)
    app.register_blueprint(submissions_bp)
    app.register_blueprint(telemetry_api_bp)

    # Register telemetry middleware
    from app.telemetry.middleware import init_telemetry
    init_telemetry(app)

    # Create tables and seed data
    with app.app_context():
        db.create_all()
        from app.models.seed import seed_database
        seed_database()

    return app
