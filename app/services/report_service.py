import csv
import io
from datetime import timezone
from zoneinfo import ZoneInfo

from flask import Response
from app.models import User, Attendance

CAIRO_TZ = ZoneInfo("Africa/Cairo")


def _to_cairo(value, fmt='%Y-%m-%d %I:%M %p'):
    """Same display-only UTC -> Africa/Cairo rule as the cairo_time Jinja filter,
    used here for the CSV export instead of a template."""
    if value is None:
        return ''
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(CAIRO_TZ).strftime(fmt)


def get_report(date_from, date_to, zone_id=None, status=None, employee_id=None):
    query = (
        Attendance.query
        .join(User, Attendance.user_id == User.id)
        .filter(Attendance.date >= date_from, Attendance.date <= date_to)
    )

    if zone_id:
        query = query.filter(Attendance.zone_id == zone_id)

    if status == 'full_shift':
        query = query.filter(Attendance.shift_status == 'full_shift')
    elif status == 'short_shift':
        query = query.filter(Attendance.shift_status == 'short_shift')
    elif status == 'active':
        query = query.filter(Attendance.status == 'active')

    if employee_id:
        query = query.filter(Attendance.user_id == employee_id)

    return query.order_by(Attendance.date.desc(), Attendance.sign_in_time.desc()).all()


STATUS_LABELS = {
    'full_shift': 'شفت كامل',
    'short_shift': 'شفت غير كامل',
    None: 'لسه ما سجلش انصراف',
}


def export_csv(rows):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        'التاريخ', 'الموظف', 'الفرع', 'وقت الحضور', 'وقت الانصراف',
        'إجمالي الساعات', 'حالة الشفت', 'متأخر', 'دقائق التأخير',
    ])

    for row in rows:
        writer.writerow([
            row.date.isoformat(),
            row.user.name,
            row.zone.name,
            _to_cairo(row.sign_in_time),
            _to_cairo(row.sign_out_time),
            f'{row.total_hours:.1f}' if row.total_hours is not None else '',
            STATUS_LABELS.get(row.shift_status, row.shift_status),
            'نعم' if row.is_late else 'لا',
            row.late_minutes or 0,
        ])

    # UTF-8 BOM so Excel opens the Arabic columns correctly instead of mojibake.
    csv_bytes = '\ufeff' + buffer.getvalue()

    return Response(
        csv_bytes,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=attendance_report.csv'},
    )
