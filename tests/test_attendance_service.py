import pytest
from datetime import datetime, date, timezone, time
from unittest.mock import patch

from app.models import User, Attendance, Zone, ShiftSetting
from app.services import attendance_service


def test_sign_in_success(app, db_session):
    user = User.query.filter_by(role='employee').first()
    # HQ coordinates: (30.0444, 31.2357)
    with patch('app.services.attendance_service._now_utc') as mock_now:
        # Mock time at 09:00 UTC (11:00 Cairo time, within 08:00 - 18:00 shift)
        mock_now.return_value = datetime(2026, 9, 24, 9, 0, 0, tzinfo=timezone.utc)
        att = attendance_service.sign_in(user, 30.0444, 31.2357)

        assert att.id is not None
        assert att.user_id == user.id
        assert att.status == 'active'
        assert att.is_late is True  # 11:00 is after 08:00 + 15m grace


def test_sign_in_outside_zone_raises(app):
    user = User.query.filter_by(role='employee').first()
    with patch('app.services.attendance_service._now_utc') as mock_now:
        mock_now.return_value = datetime(2026, 9, 24, 9, 0, 0, tzinfo=timezone.utc)
        # Alexandria coordinates (far from HQ)
        with pytest.raises(ValueError) as exc:
            attendance_service.sign_in(user, 31.2001, 29.9187)
        assert "برا نطاق الفرع" in str(exc.value)


def test_sign_in_outside_window_raises(app):
    user = User.query.filter_by(role='employee').first()
    with patch('app.services.attendance_service._now_utc') as mock_now:
        # 03:00 UTC = 05:00 Cairo time (before 08:00 shift start)
        mock_now.return_value = datetime(2026, 9, 24, 3, 0, 0, tzinfo=timezone.utc)
        with pytest.raises(ValueError) as exc:
            attendance_service.sign_in(user, 30.0444, 31.2357)
        assert "برا وقت تسجيل الحضور" in str(exc.value)


def test_sign_in_already_signed_in_raises(app, db_session):
    user = User.query.filter_by(role='employee').first()
    with patch('app.services.attendance_service._now_utc') as mock_now:
        mock_now.return_value = datetime(2026, 9, 24, 9, 0, 0, tzinfo=timezone.utc)
        attendance_service.sign_in(user, 30.0444, 31.2357)

        with pytest.raises(ValueError) as exc:
            attendance_service.sign_in(user, 30.0444, 31.2357)
        assert "بالفعل النهاردة" in str(exc.value)


def test_sign_out_without_sign_in_raises(app):
    user = User.query.filter_by(role='employee').first()
    with pytest.raises(ValueError) as exc:
        attendance_service.sign_out(user, 30.0444, 31.2357)
    assert "لسه ما سجلتش حضور" in str(exc.value)


def test_sign_out_full_shift(app, db_session):
    user = User.query.filter_by(role='employee').first()
    sign_in_dt = datetime(2026, 9, 24, 6, 0, 0, tzinfo=timezone.utc)
    sign_out_dt = datetime(2026, 9, 24, 10, 0, 0, tzinfo=timezone.utc)  # 4 hours worked >= 3.0 min_full_shift_hours

    with patch('app.services.attendance_service._now_utc') as mock_now:
        mock_now.return_value = sign_in_dt
        attendance_service.sign_in(user, 30.0444, 31.2357)

    with patch('app.services.attendance_service._now_utc') as mock_now:
        mock_now.return_value = sign_out_dt
        att = attendance_service.sign_out(user, 30.0444, 31.2357)

        assert att.status == 'completed'
        assert att.total_hours == pytest.approx(4.0)
        assert att.shift_status == 'full_shift'


def test_sign_out_short_shift(app, db_session):
    user = User.query.filter_by(role='employee').first()
    sign_in_dt = datetime(2026, 9, 24, 6, 0, 0, tzinfo=timezone.utc)
    sign_out_dt = datetime(2026, 9, 24, 7, 30, 0, tzinfo=timezone.utc)  # 1.5 hours worked < 3.0 min_full_shift_hours

    with patch('app.services.attendance_service._now_utc') as mock_now:
        mock_now.return_value = sign_in_dt
        attendance_service.sign_in(user, 30.0444, 31.2357)

    with patch('app.services.attendance_service._now_utc') as mock_now:
        mock_now.return_value = sign_out_dt
        att = attendance_service.sign_out(user, 30.0444, 31.2357)

        assert att.status == 'completed'
        assert att.total_hours == pytest.approx(1.5)
        assert att.shift_status == 'short_shift'


def test_get_dashboard_context(app, db_session):
    user = User.query.filter_by(role='employee').first()
    ctx = attendance_service.get_dashboard_context(user, None, live_lat=30.0444, live_lng=31.2357)
    assert ctx['zone'] is not None
    assert ctx['shift'] is not None
    assert ctx['live_status']['inside'] is True
    assert ctx['elapsed_hours'] == 0.0


def test_get_history(app, db_session):
    user = User.query.filter_by(role='employee').first()
    history_before = attendance_service.get_history(user)
    assert len(history_before) == 0

    with patch('app.services.attendance_service._now_utc') as mock_now:
        mock_now.return_value = datetime(2026, 9, 24, 9, 0, 0, tzinfo=timezone.utc)
        attendance_service.sign_in(user, 30.0444, 31.2357)

    history_after = attendance_service.get_history(user)
    assert len(history_after) == 1
