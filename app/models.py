from flask_login import UserMixin
from datetime import datetime,date
from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id'), index=True)
    shift_setting_id = db.Column(db.Integer, db.ForeignKey('shift_settings.id'), index=True)

    name = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.Enum('admin', 'employee', name='user_role'), nullable=False, default='employee')
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # relationships
    attendances = db.relationship('Attendance', backref='user', lazy=True)


class Zone(db.Model):
    __tablename__ = "zones"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    radius_meters = db.Column(db.Integer, nullable=False, default=50)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship('User', backref='zone', lazy=True)
    


class ShiftSetting(db.Model):
    __tablename__ = "shift_settings"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    shift_start_time = db.Column(db.Time, nullable=False)          # بداية الشفت الرسمية
    sign_in_end_time = db.Column(db.Time, nullable=False)          # آخر وقت مسموح فيه تسجيل حضور
    grace_period_minutes = db.Column(db.Integer, nullable=False, default=15)
    min_full_shift_hours = db.Column(db.Float, nullable=False, default=3.0)

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # relationship
    users = db.relationship('User', backref='shift_setting', lazy=True)


class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id'), nullable=False, index=True)

    date = db.Column(db.Date, nullable=False, default=date.today, index=True)

    sign_in_time = db.Column(db.DateTime, nullable=True)
    sign_out_time = db.Column(db.DateTime, nullable=True)

    sign_in_latitude = db.Column(db.Float, nullable=True)
    sign_in_longitude = db.Column(db.Float, nullable=True)
    sign_in_distance = db.Column(db.Float, nullable=True)   # بالمتر، وقت التسجيل

    sign_out_latitude = db.Column(db.Float, nullable=True)
    sign_out_longitude = db.Column(db.Float, nullable=True)
    sign_out_distance = db.Column(db.Float, nullable=True)

    total_hours = db.Column(db.Float, nullable=True)

    is_late = db.Column(db.Boolean, default=False)
    late_minutes = db.Column(db.Integer, default=0)

    status = db.Column(
        db.Enum('active', 'completed', name='attendance_status'),
        nullable=False,
        default='active'
    )
    shift_status = db.Column(
        db.Enum('full_shift', 'short_shift', name='attendance_shift_status'),
        nullable=True
    )

    # relationship
    zone = db.relationship('Zone', backref='attendances', lazy=True)


class WebAuthnCredential(db.Model):
    """Batch 12 — one row per registered platform authenticator (Face ID / Touch ID /
    Windows Hello / Android biometrics) a user has enrolled. A user can register more
    than one device."""
    __tablename__ = "webauthn_credentials"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    credential_id = db.Column(db.String(255), nullable=False, unique=True)  # base64url, from the authenticator
    public_key = db.Column(db.LargeBinary, nullable=False)
    sign_count = db.Column(db.Integer, nullable=False, default=0)

    device_type = db.Column(db.String(20), nullable=True)   # 'single_device' / 'multi_device'
    backed_up = db.Column(db.Boolean, nullable=False, default=False)
    nickname = db.Column(db.String(100), nullable=True)     # user-supplied, e.g. "تليفوني"

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime, nullable=True)

    # relationship
    user = db.relationship('User', backref='webauthn_credentials', lazy=True)