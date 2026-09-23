# seed_demo_data.py
#
# NOT part of Batch 10 itself — Batches 4 (Shift Settings CRUD), 7 (Sign-In) and
# 8 (Sign-Out) are what would normally create ShiftSetting rows and Attendance
# rows through the UI. Since those batches aren't built yet, this script writes
# directly to the models (like seed.py already does for users) so the Batch 10
# admin dashboard has real rows to query and display instead of all zeros.
#
# Safe to re-run: it wipes and re-creates zones/shifts/employees/attendance only
# (never touches the admin user).

import random
from datetime import date, datetime, time, timedelta, timezone

from app import create_app
from app.extensions import db
from app.models import User, Zone, ShiftSetting, Attendance
from app.services.auth_service import create_user
from app.services.zone_service import create_zone

app = create_app()

EMPLOYEE_NAMES = [
    "أحمد محمد", "محمد السيد", "سارة خالد", "علي محمود", "منى حسن",
    "كريم عادل", "هدى إبراهيم", "يوسف طارق", "نورا فتحي", "مصطفى جمال",
    "ريم صلاح", "عمر رشدي", "داليا فؤاد", "حسام الدين", "ياسمين عمر",
]

with app.app_context():
    # wipe demo data only (keep the admin user)
    Attendance.query.delete()
    User.query.filter_by(role='employee').delete()
    ShiftSetting.query.delete()
    Zone.query.delete()
    db.session.commit()

    zones = [
        create_zone("فرع القاهرة", 30.0444, 31.2357, 50),
        create_zone("فرع الإسكندرية", 31.2001, 29.9187, 75),
        create_zone("فرع الجيزة", 30.0131, 31.2089, 60),
    ]

    morning = ShiftSetting(
        name="صباحي", shift_start_time=time(8, 0), sign_in_end_time=time(10, 0),
        grace_period_minutes=15, min_full_shift_hours=3.0,
    )
    evening = ShiftSetting(
        name="مسائي", shift_start_time=time(16, 0), sign_in_end_time=time(18, 0),
        grace_period_minutes=10, min_full_shift_hours=3.0,
    )
    db.session.add_all([morning, evening])
    db.session.commit()
    shifts = [morning, evening]

    employees = []
    for name in EMPLOYEE_NAMES:
        zone = random.choice(zones)
        shift = random.choice(shifts)
        emp = create_user(name=name, password="123456", role="employee",
                           zone_id=zone.id, shift_setting_id=shift.id)
        employees.append(emp)

    today = date.today()
    now = datetime.now(timezone.utc)

    # roughly matches the mockup's mix: mostly full shift, some short, a few absent
    outcomes = (["full_shift"] * 9) + (["short_shift"] * 3) + (["absent"] * 3)
    random.shuffle(outcomes)

    for emp, outcome in zip(employees, outcomes):
        if outcome == "absent":
            continue

        zone = Zone.query.get(emp.zone_id)
        sign_in = now.replace(hour=8, minute=random.randint(0, 25), second=0, microsecond=0) \
            - timedelta(hours=random.choice([0, 8]))  # vary the day a bit
        is_late = sign_in.time() > time(8, 15)
        late_minutes = max(0, (sign_in.hour * 60 + sign_in.minute) - (8 * 60 + 15)) if is_late else 0

        hours = round(random.uniform(3.2, 8.5), 1) if outcome == "full_shift" else round(random.uniform(1.0, 2.8), 1)
        sign_out = sign_in + timedelta(hours=hours)

        db.session.add(Attendance(
            user_id=emp.id, zone_id=zone.id, date=today,
            sign_in_time=sign_in, sign_out_time=sign_out,
            sign_in_latitude=zone.latitude, sign_in_longitude=zone.longitude, sign_in_distance=round(random.uniform(2, 45), 1),
            sign_out_latitude=zone.latitude, sign_out_longitude=zone.longitude, sign_out_distance=round(random.uniform(2, 45), 1),
            total_hours=hours, is_late=is_late, late_minutes=late_minutes,
            status='completed', shift_status=outcome,
        ))

    db.session.commit()
    print(f"تم إنشاء {len(zones)} فروع، {len(shifts)} شفتات، {len(employees)} موظف، وبيانات حضور تجريبية لليوم.")
