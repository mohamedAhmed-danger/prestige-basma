import pytest
from datetime import time
from app import create_app
from app.extensions import db as _db
from app.models import User, Zone, ShiftSetting


@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test_secret_key',
        'WTF_CSRF_ENABLED': False,
        'WEBAUTHN_RP_ID': 'localhost',
        'WEBAUTHN_ORIGIN': 'http://localhost:5000',
    })

    with app.app_context():
        _db.create_all()

        # Create default test zone & shift
        zone = Zone(name="Main HQ", latitude=30.0444, longitude=31.2357, radius_meters=100)
        shift = ShiftSetting(
            name="Morning Shift",
            shift_start_time=time(8, 0),
            sign_in_end_time=time(18, 0),
            grace_period_minutes=15,
            min_full_shift_hours=3.0,
        )
        _db.session.add_all([zone, shift])
        _db.session.commit()

        # Create default admin and employee
        admin = User(
            name="Admin User",
            password_hash="pbkdf2:sha256:test",
            role="admin",
            zone_id=zone.id,
            shift_setting_id=shift.id,
        )
        employee = User(
            name="Employee User",
            password_hash="pbkdf2:sha256:test",
            role="employee",
            zone_id=zone.id,
            shift_setting_id=shift.id,
        )
        _db.session.add_all([admin, employee])
        _db.session.commit()

        yield app

        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db_session(app):
    return _db.session
