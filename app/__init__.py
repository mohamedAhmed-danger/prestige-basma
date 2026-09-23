import os
from datetime import timezone
from zoneinfo import ZoneInfo
from flask import Flask, render_template
from app.config import Config
from app.extensions import db, migrate, login_manager
from app.models import User

CAIRO_TZ = ZoneInfo("Africa/Cairo")



def create_app():
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # models must be imported before migrate can see them
    from app.models import  User,ShiftSetting,Attendance,Zone

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.employee import employee_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(employee_bp)

    @app.template_filter('cairo_time')
    def cairo_time(value, fmt='%I:%M %p'):
        """Display-only conversion of a stored UTC datetime to Africa/Cairo local time.
        Egypt has no fixed UTC offset (DST toggled in recent years), so this always
        goes through zoneinfo — never a hardcoded +2/+3."""
        if value is None:
            return '—'
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(CAIRO_TZ).strftime(fmt)

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app