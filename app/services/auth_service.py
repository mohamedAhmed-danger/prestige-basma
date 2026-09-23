from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.services.validators import validate_username, validate_password
from app.models import User


def authenticate_user(username, password):

    if not username or not password:
        return None

    user = User.query.filter_by(name=username.strip()).first()

    if user and user.is_active and check_password_hash(user.password_hash, password):
        return user

    return None


def create_user(name, password, role='employee', zone_id=None, shift_setting_id=None):

    name = validate_username(name)
    validate_password(password)

    if User.query.filter_by(name=name).first():
        raise ValueError('اسم المستخدم ده مستخدم بالفعل')

    user = User(
        name=name,
        password_hash=generate_password_hash(password),
        role=role,
        zone_id=zone_id,
        shift_setting_id=shift_setting_id,
    )
    db.session.add(user)
    db.session.commit()
    return user


def update_user(user_id, name=None, password=None, zone_id=None, shift_setting_id=None, is_active=True):
    user = User.query.get_or_404(user_id)
    if name and name.strip():
        name = validate_username(name)
        existing = User.query.filter_by(name=name).first()
        if existing and existing.id != user_id:
            raise ValueError('اسم المستخدم ده مستخدم بالفعل')
        user.name = name

    if password and password.strip():
        validate_password(password)
        user.password_hash = generate_password_hash(password)

    user.zone_id = int(zone_id) if zone_id else None
    user.shift_setting_id = int(shift_setting_id) if shift_setting_id else None
    user.is_active = bool(is_active)

    db.session.commit()
    return user


def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        raise ValueError('لا يمكن حذف مدير النظام')
    db.session.delete(user)
    db.session.commit()