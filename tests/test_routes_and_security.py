import pytest
from flask import url_for
from app.models import User, Zone, ShiftSetting


def test_public_routes(client):
    res = client.get('/')
    assert res.status_code == 302
    assert '/login' in res.location

    res_login = client.get('/login')
    assert res_login.status_code == 200
    assert "تسجيل الدخول" in res_login.get_data(as_text=True)


def test_unauthenticated_access_protected_routes(client):
    protected_urls = [
        '/employee/dashboard',
        '/employee/attendance',
        '/employee/profile',
        '/admin/dashboard',
        '/admin/employees',
        '/admin/shifts',
        '/admin/zones',
        '/admin/reports',
        '/admin/settings',
    ]
    for url in protected_urls:
        res = client.get(url)
        assert res.status_code == 302
        assert '/login' in res.location


def test_employee_cannot_access_admin_routes(client, app):
    employee = User.query.filter_by(role='employee').first()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(employee.id)

    admin_urls = [
        '/admin/dashboard',
        '/admin/employees',
        '/admin/shifts',
        '/admin/zones',
        '/admin/reports',
        '/admin/settings',
    ]
    for url in admin_urls:
        res = client.get(url)
        assert res.status_code == 302 or res.status_code == 403


def test_admin_full_flow_page_renders(client, app):
    admin = User.query.filter_by(role='admin').first()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin.id)

    # Admin Dashboard
    res_dash = client.get('/admin/dashboard')
    assert res_dash.status_code == 200

    # Employees List & Create Page
    res_emp = client.get('/admin/employees')
    assert res_emp.status_code == 200
    res_emp_create = client.get('/admin/employees/create')
    assert res_emp_create.status_code == 200

    # Shifts List & Create Page
    res_shifts = client.get('/admin/shifts')
    assert res_shifts.status_code == 200
    res_shifts_create = client.get('/admin/shifts/create')
    assert res_shifts_create.status_code == 200

    # Zones List & Create Page
    res_zones = client.get('/admin/zones')
    assert res_zones.status_code == 200
    res_zones_create = client.get('/admin/zones/create')
    assert res_zones_create.status_code == 200

    # Reports & Settings Page
    res_reports = client.get('/admin/reports')
    assert res_reports.status_code == 200
    res_settings = client.get('/admin/settings')
    assert res_settings.status_code == 200


def test_employee_full_flow_page_renders(client, app):
    employee = User.query.filter_by(role='employee').first()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(employee.id)

    # Dashboard
    res_dash = client.get('/employee/dashboard')
    assert res_dash.status_code == 200

    # Attendance History
    res_history = client.get('/employee/attendance')
    assert res_history.status_code == 200

    # Profile
    res_profile = client.get('/employee/profile')
    assert res_profile.status_code == 200

    # WebAuthn register page
    res_webauthn = client.get('/employee/webauthn/register')
    assert res_webauthn.status_code == 200
