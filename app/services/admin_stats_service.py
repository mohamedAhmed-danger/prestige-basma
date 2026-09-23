from datetime import date
from app.models import User, Zone, Attendance


AR_WEEKDAYS = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
AR_MONTHS = [
    'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
    'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر',
]


def format_arabic_date(d):
    return f"{AR_WEEKDAYS[d.weekday()]}، {d.day} {AR_MONTHS[d.month - 1]} {d.year}"


def get_dashboard_kpis(target_date=None):
    """KPI + donut numbers for 'today' (or a given date). Read-only, no mutation."""
    target_date = target_date or date.today()

    total_employees = User.query.filter_by(role='employee').count()
    today_rows = Attendance.query.filter_by(date=target_date).all()

    full_shift_count = sum(1 for a in today_rows if a.shift_status == 'full_shift')
    short_shift_count = sum(1 for a in today_rows if a.shift_status == 'short_shift')
    in_progress_count = sum(1 for a in today_rows if a.status == 'active')
    present_count = len(today_rows)
    absent_count = max(total_employees - present_count, 0)

    return {
        'total_employees': total_employees,
        'present_count': present_count,
        'full_shift_count': full_shift_count,
        'short_shift_count': short_shift_count,
        'in_progress_count': in_progress_count,
        'absent_count': absent_count,
    }


def get_zones_overview():
    return Zone.query.order_by(Zone.id).all()


def get_daily_report(target_date, zone_id=None, status=None, search=None):
    """Filtered attendance rows for the daily report table (date/zone/status/name)."""
    query = (
        Attendance.query
        .join(User, Attendance.user_id == User.id)
        .filter(Attendance.date == target_date)
    )

    if zone_id:
        query = query.filter(Attendance.zone_id == zone_id)

    if status == 'full_shift':
        query = query.filter(Attendance.shift_status == 'full_shift')
    elif status == 'short_shift':
        query = query.filter(Attendance.shift_status == 'short_shift')
    elif status == 'active':
        query = query.filter(Attendance.status == 'active')

    if search:
        query = query.filter(User.name.ilike(f'%{search.strip()}%'))

    return query.order_by(Attendance.sign_in_time.desc()).all()


def get_weekly_trend(target_date=None):
    """Calculates weekly attendance trend (last 7 days) for dashboard chart."""
    from datetime import timedelta
    target_date = target_date or date.today()
    start_date = target_date - timedelta(days=6)
    
    days_data = []
    curr = start_date
    while curr <= target_date:
        rows = Attendance.query.filter_by(date=curr).all()
        full_cnt = sum(1 for a in rows if a.shift_status == 'full_shift')
        short_cnt = sum(1 for a in rows if a.shift_status == 'short_shift')
        active_cnt = sum(1 for a in rows if a.status == 'active')
        
        days_data.append({
            'day_name': AR_WEEKDAYS[curr.weekday()],
            'date_str': curr.strftime('%d/%m'),
            'full_shift': full_cnt,
            'short_shift': short_cnt,
            'active': active_cnt
        })
        curr += timedelta(days=1)
        
    return days_data

