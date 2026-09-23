import pytest
from datetime import time
from app.models import ShiftSetting, Zone, User
from app.services import shift_service, zone_service, auth_service


# --- Shift Service Tests ---------------------------------------------------

def test_create_shift_success(app, db_session):
    shift = shift_service.create_shift("Night Shift", "22:00", "23:59", 10, 4.0)
    assert shift.id is not None
    assert shift.name == "Night Shift"
    assert shift.shift_start_time == time(22, 0)
    assert shift.sign_in_end_time == time(23, 59)
    assert shift.grace_period_minutes == 10
    assert shift.min_full_shift_hours == 4.0


def test_create_shift_validations(app):
    # Empty name
    with pytest.raises(ValueError) as exc:
        shift_service.create_shift("   ", "08:00", "12:00", 15, 3.0)
    assert "اسم الشفت مطلوب" in str(exc.value)

    # Invalid start/end time order
    with pytest.raises(ValueError) as exc:
        shift_service.create_shift("Bad Time", "14:00", "10:00", 15, 3.0)
    assert "قبل آخر وقت" in str(exc.value)

    # Negative grace period
    with pytest.raises(ValueError) as exc:
        shift_service.create_shift("Bad Grace", "08:00", "12:00", -5, 3.0)
    assert "فترة السماح" in str(exc.value)

    # Duplicate name
    with pytest.raises(ValueError) as exc:
        shift_service.create_shift("Morning Shift", "08:00", "12:00", 15, 3.0)
    assert "مستخدم بالفعل" in str(exc.value)


def test_update_and_delete_shift(app, db_session):
    shift = shift_service.create_shift("Temp Shift", "09:00", "13:00", 15, 3.0)
    shift_service.update_shift(shift.id, "Temp Shift Updated", "09:30", "13:30", 20, 3.5)
    
    updated = ShiftSetting.query.get(shift.id)
    assert updated.name == "Temp Shift Updated"
    assert updated.grace_period_minutes == 20

    # Delete shift without users
    shift_service.delete_shift(shift.id)
    assert ShiftSetting.query.get(shift.id) is None


def test_delete_shift_with_users_fails(app):
    # Morning Shift has assigned users in fixture
    default_shift = ShiftSetting.query.filter_by(name="Morning Shift").first()
    with pytest.raises(ValueError) as exc:
        shift_service.delete_shift(default_shift.id)
    assert "فيه موظفين متعينين عليه" in str(exc.value)


# --- Zone Service Tests ----------------------------------------------------

def test_create_zone_success(app, db_session):
    zone = zone_service.create_zone("Alex Branch", 31.2001, 29.9187, 150)
    assert zone.id is not None
    assert zone.name == "Alex Branch"
    assert zone.latitude == 31.2001
    assert zone.radius_meters == 150


def test_create_zone_validations(app):
    # Invalid coordinates
    with pytest.raises(ValueError) as exc:
        zone_service.create_zone("Bad Lat", 95.0, 30.0, 100)
    assert "خط العرض" in str(exc.value)

    # Negative radius
    with pytest.raises(ValueError) as exc:
        zone_service.create_zone("Bad Radius", 30.0, 30.0, -10)
    assert "رقم موجب" in str(exc.value)

    # Duplicate name
    with pytest.raises(ValueError) as exc:
        zone_service.create_zone("Main HQ", 30.0, 30.0, 100)
    assert "مستخدم بالفعل" in str(exc.value)


def test_delete_zone_with_users_fails(app):
    default_zone = Zone.query.filter_by(name="Main HQ").first()
    with pytest.raises(ValueError) as exc:
        zone_service.delete_zone(default_zone.id)
    assert "فيه موظفين متعينين عليه" in str(exc.value)


# --- Auth & Employee Service Tests -----------------------------------------

def test_create_and_manage_user(app, db_session):
    zone = Zone.query.first()
    shift = ShiftSetting.query.first()

    new_user = auth_service.create_user(
        name="New Employee",
        password="Password123",
        role="employee",
        zone_id=zone.id,
        shift_setting_id=shift.id,
    )
    assert new_user.id is not None
    assert auth_service.authenticate_user("New Employee", "Password123") is not None

    # Duplicate user name
    with pytest.raises(ValueError) as exc:
        auth_service.create_user("New Employee", "Password123", "employee")
    assert "مستخدم بالفعل" in str(exc.value)

    # Update user
    auth_service.update_user(new_user.id, name="Updated Employee", is_active=False)
    updated_user = User.query.get(new_user.id)
    assert updated_user.name == "Updated Employee"
    assert updated_user.is_active is False

    # Delete user
    auth_service.delete_user(new_user.id)
    assert User.query.get(new_user.id) is None
