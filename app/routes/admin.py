from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.utils import admin_required
from app.models import Zone, User, ShiftSetting
from app.services.zone_service import create_zone, update_zone, delete_zone
from app.services.shift_service import create_shift, update_shift, delete_shift
from app.services.admin_stats_service import (
    get_dashboard_kpis,
    get_zones_overview,
    get_daily_report,
    get_weekly_trend,
    format_arabic_date,
)
from app.services.report_service import get_report, export_csv, export_excel

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Server clock is the only source of truth for "today" — never client time.
    date_param = request.args.get('date')
    try:
        target_date = datetime.strptime(date_param, '%Y-%m-%d').date() if date_param else date.today()
    except ValueError:
        target_date = date.today()

    zone_id = request.args.get('zone_id', type=int)
    status = request.args.get('status') or None
    search = request.args.get('q') or None

    kpis = get_dashboard_kpis()
    zones = get_zones_overview()
    report_rows = get_daily_report(target_date, zone_id=zone_id, status=status, search=search)
    weekly_trend = get_weekly_trend(target_date)

    return render_template(
        'admin/dashboard.html',
        kpis=kpis,
        zones=zones,
        report_rows=report_rows,
        weekly_trend=weekly_trend,
        target_date=target_date,
        today_display=format_arabic_date(date.today()),
        filters={'zone_id': zone_id, 'status': status, 'q': search or ''},
    )


@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    today = date.today()

    date_from_param = request.args.get('date_from')
    date_to_param = request.args.get('date_to')

    try:
        date_from = datetime.strptime(date_from_param, '%Y-%m-%d').date() if date_from_param else today - timedelta(days=6)
    except ValueError:
        date_from = today - timedelta(days=6)

    try:
        date_to = datetime.strptime(date_to_param, '%Y-%m-%d').date() if date_to_param else today
    except ValueError:
        date_to = today

    # keep the range sane regardless of what was typed into the two date inputs
    if date_from > date_to:
        date_from, date_to = date_to, date_from

    zone_id = request.args.get('zone_id', type=int)
    status = request.args.get('status') or None
    employee_id = request.args.get('employee_id', type=int)

    rows = get_report(date_from, date_to, zone_id=zone_id, status=status, employee_id=employee_id)

    if request.args.get('export') in ('excel', 'xlsx'):
        return export_excel(rows)
    elif request.args.get('export') == 'csv':
        return export_csv(rows)

    zones_list = Zone.query.order_by(Zone.id).all()
    employees = User.query.filter_by(role='employee').order_by(User.name).all()

    return render_template(
        'admin/reports.html',
        rows=rows,
        zones=zones_list,
        employees=employees,
        date_from=date_from,
        date_to=date_to,
        today_display=format_arabic_date(today),
        filters={'zone_id': zone_id, 'status': status, 'employee_id': employee_id},
    )


@admin_bp.route('/zones')
@login_required
@admin_required
def zones():
    all_zones = Zone.query.order_by(Zone.id).all()
    return render_template('admin/zones/list.html', zones=all_zones)


@admin_bp.route('/zones/create', methods=['GET', 'POST'])
@login_required
@admin_required
def zones_create():
    if request.method == 'POST':
        try:
            create_zone(
                request.form.get('name'),
                request.form.get('latitude'),
                request.form.get('longitude'),
                request.form.get('radius_meters'),
            )
            flash('تم إضافة الفرع', 'success')
            return redirect(url_for('admin.zones'))
        except ValueError as e:
            flash(str(e), 'danger')
    return render_template('admin/zones/create.html')


@admin_bp.route('/zones/<int:zone_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def zones_edit(zone_id):
    zone = Zone.query.get_or_404(zone_id)
    if request.method == 'POST':
        try:
            update_zone(
                zone_id,
                request.form.get('name'),
                request.form.get('latitude'),
                request.form.get('longitude'),
                request.form.get('radius_meters'),
                is_active=bool(request.form.get('is_active')),
            )
            flash('تم تعديل الفرع', 'success')
            return redirect(url_for('admin.zones'))
        except ValueError as e:
            flash(str(e), 'danger')
    return render_template('admin/zones/edit.html', zone=zone)


@admin_bp.route('/zones/<int:zone_id>/delete', methods=['POST'])
@login_required
@admin_required
def zones_delete(zone_id):
    try:
        delete_zone(zone_id)
        flash('تم حذف الفرع', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    return redirect(url_for('admin.zones'))


@admin_bp.route('/shifts')
@login_required
@admin_required
def shifts():
    all_shifts = ShiftSetting.query.order_by(ShiftSetting.id).all()
    return render_template('admin/shifts/list.html', shifts=all_shifts)


@admin_bp.route('/shifts/create', methods=['GET', 'POST'])
@login_required
@admin_required
def shifts_create():
    if request.method == 'POST':
        try:
            create_shift(
                request.form.get('name'),
                request.form.get('shift_start_time'),
                request.form.get('sign_in_end_time'),
                request.form.get('grace_period_minutes'),
                request.form.get('min_full_shift_hours'),
            )
            flash('تم إضافة الشفت', 'success')
            return redirect(url_for('admin.shifts'))
        except ValueError as e:
            flash(str(e), 'danger')
    return render_template('admin/shifts/create.html')


@admin_bp.route('/shifts/<int:shift_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def shifts_edit(shift_id):
    shift = ShiftSetting.query.get_or_404(shift_id)
    if request.method == 'POST':
        try:
            update_shift(
                shift_id,
                request.form.get('name'),
                request.form.get('shift_start_time'),
                request.form.get('sign_in_end_time'),
                request.form.get('grace_period_minutes'),
                request.form.get('min_full_shift_hours'),
                is_active=bool(request.form.get('is_active')),
            )
            flash('تم تعديل الشفت', 'success')
            return redirect(url_for('admin.shifts'))
        except ValueError as e:
            flash(str(e), 'danger')
    return render_template('admin/shifts/edit.html', shift=shift)


@admin_bp.route('/shifts/<int:shift_id>/delete', methods=['POST'])
@login_required
@admin_required
def shifts_delete(shift_id):
    try:
        delete_shift(shift_id)
        flash('تم حذف الشفت', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    return redirect(url_for('admin.shifts'))


# --- Employees Management Routes ----------------------------------------------

@admin_bp.route('/employees')
@login_required
@admin_required
def employees():
    all_employees = User.query.filter_by(role='employee').order_by(User.id.desc()).all()
    return render_template('admin/employees/list.html', employees=all_employees)


@admin_bp.route('/employees/create', methods=['GET', 'POST'])
@login_required
@admin_required
def employees_create():
    if request.method == 'POST':
        try:
            from app.services.auth_service import create_user
            create_user(
                name=request.form.get('name'),
                password=request.form.get('password'),
                role='employee',
                zone_id=request.form.get('zone_id', type=int),
                shift_setting_id=request.form.get('shift_setting_id', type=int),
            )
            flash('تم إضافة الموظف بنجاح', 'success')
            return redirect(url_for('admin.employees'))
        except ValueError as e:
            flash(str(e), 'danger')

    zones_list = Zone.query.filter_by(is_active=True).all()
    shifts_list = ShiftSetting.query.filter_by(is_active=True).all()
    return render_template('admin/employees/create.html', zones=zones_list, shifts=shifts_list)


@admin_bp.route('/employees/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def employees_edit(user_id):
    emp = User.query.get_or_404(user_id)
    if emp.role == 'admin':
        flash('لا يمكن تعديل بيانات المدير من هذه الصفحة', 'danger')
        return redirect(url_for('admin.employees'))

    if request.method == 'POST':
        try:
            from app.services.auth_service import update_user
            update_user(
                user_id=user_id,
                name=request.form.get('name'),
                password=request.form.get('password'),
                zone_id=request.form.get('zone_id'),
                shift_setting_id=request.form.get('shift_setting_id'),
                is_active=bool(request.form.get('is_active')),
            )
            flash('تم تعديل بيانات الموظف بنجاح', 'success')
            return redirect(url_for('admin.employees'))
        except ValueError as e:
            flash(str(e), 'danger')

    zones_list = Zone.query.filter_by(is_active=True).all()
    shifts_list = ShiftSetting.query.filter_by(is_active=True).all()
    return render_template('admin/employees/edit.html', employee=emp, zones=zones_list, shifts=shifts_list)


@admin_bp.route('/employees/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def employees_delete(user_id):
    try:
        from app.services.auth_service import delete_user
        delete_user(user_id)
        flash('تم حذف الموظف بنجاح', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    return redirect(url_for('admin.employees'))


@admin_bp.route('/employees/<int:user_id>/reset-devices', methods=['POST'])
@login_required
@admin_required
def employees_reset_devices(user_id):
    emp = User.query.get_or_404(user_id)
    try:
        from app.models import WebAuthnCredential
        from app.extensions import db
        WebAuthnCredential.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        flash(f'تم إزالة الأجهزة المسجلة للموظف ({emp.name}) بنجاح ويمكنه الآن تسجيل جهاز جديد', 'success')
    except Exception as e:
        flash(f'حصل خطأ: {e}', 'danger')
    return redirect(url_for('admin.employees'))


# --- System Settings Routes --------------------------------------------------

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    if request.method == 'POST':
        flash('تم حفظ إعدادات النظام بنجاح', 'success')
        return redirect(url_for('admin.settings'))

    from app.models import User, Zone, ShiftSetting, Attendance, WebAuthnCredential
    stats = {
        'total_employees': User.query.filter_by(role='employee').count(),
        'total_zones': Zone.query.count(),
        'total_shifts': ShiftSetting.query.count(),
        'total_attendance': Attendance.query.count(),
        'registered_devices': WebAuthnCredential.query.count(),
    }

    return render_template('admin/settings.html', stats=stats)