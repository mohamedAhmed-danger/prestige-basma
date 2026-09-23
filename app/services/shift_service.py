from datetime import datetime

from app.extensions import db
from app.models import ShiftSetting


def _parse_time(value, field_label):
    if isinstance(value, str):
        try:
            return datetime.strptime(value, '%H:%M').time()
        except ValueError:
            raise ValueError(f'{field_label} لازم يكون وقت صحيح (HH:MM)')
    return value


def validate_shift(name, shift_start_time, sign_in_end_time, grace_period_minutes, min_full_shift_hours):
    if not name or not name.strip():
        raise ValueError('اسم الشفت مطلوب')

    shift_start_time = _parse_time(shift_start_time, 'بداية الشفت')
    sign_in_end_time = _parse_time(sign_in_end_time, 'آخر وقت لتسجيل الحضور')

    if shift_start_time is None or sign_in_end_time is None:
        raise ValueError('بداية الشفت وآخر وقت لتسجيل الحضور لازم يتحددوا')

    if shift_start_time >= sign_in_end_time:
        raise ValueError('بداية الشفت لازم تكون قبل آخر وقت لتسجيل الحضور')

    try:
        grace_period_minutes = int(grace_period_minutes)
    except (TypeError, ValueError):
        raise ValueError('فترة السماح لازم تكون رقم')

    if grace_period_minutes < 0:
        raise ValueError('فترة السماح لازم تكون صفر أو أكبر')

    try:
        min_full_shift_hours = float(min_full_shift_hours)
    except (TypeError, ValueError):
        raise ValueError('أقل عدد ساعات لشفت كامل لازم يكون رقم')

    if min_full_shift_hours <= 0:
        raise ValueError('أقل عدد ساعات لشفت كامل لازم يكون رقم موجب')

    return name.strip(), shift_start_time, sign_in_end_time, grace_period_minutes, min_full_shift_hours


def create_shift(name, shift_start_time, sign_in_end_time, grace_period_minutes, min_full_shift_hours):
    name, shift_start_time, sign_in_end_time, grace_period_minutes, min_full_shift_hours = validate_shift(
        name, shift_start_time, sign_in_end_time, grace_period_minutes, min_full_shift_hours
    )

    if ShiftSetting.query.filter_by(name=name).first():
        raise ValueError('اسم الشفت ده مستخدم بالفعل')

    shift = ShiftSetting(
        name=name,
        shift_start_time=shift_start_time,
        sign_in_end_time=sign_in_end_time,
        grace_period_minutes=grace_period_minutes,
        min_full_shift_hours=min_full_shift_hours,
    )
    db.session.add(shift)
    db.session.commit()
    return shift


def update_shift(shift_id, name, shift_start_time, sign_in_end_time, grace_period_minutes,
                  min_full_shift_hours, is_active=True):
    shift = ShiftSetting.query.get_or_404(shift_id)
    name, shift_start_time, sign_in_end_time, grace_period_minutes, min_full_shift_hours = validate_shift(
        name, shift_start_time, sign_in_end_time, grace_period_minutes, min_full_shift_hours
    )

    existing = ShiftSetting.query.filter(ShiftSetting.name == name, ShiftSetting.id != shift_id).first()
    if existing:
        raise ValueError('اسم الشفت ده مستخدم بالفعل')

    shift.name = name
    shift.shift_start_time = shift_start_time
    shift.sign_in_end_time = sign_in_end_time
    shift.grace_period_minutes = grace_period_minutes
    shift.min_full_shift_hours = min_full_shift_hours
    shift.is_active = is_active
    db.session.commit()
    return shift


def delete_shift(shift_id):
    shift = ShiftSetting.query.get_or_404(shift_id)

    if shift.users:
        raise ValueError('مينفعش تمسح شفت لسه فيه موظفين متعينين عليه')

    db.session.delete(shift)
    db.session.commit()
