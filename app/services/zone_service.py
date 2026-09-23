from app.extensions import db
from app.models import Zone



def validate_zone(name, latitude, longitude, radius_meters):
    if not name or not name.strip():
        raise ValueError('اسم الفرع مطلوب')

    try:
        latitude = float(latitude)
        longitude = float(longitude)
        radius_meters = int(radius_meters)
    except (TypeError, ValueError):
        raise ValueError('الإحداثيات والمسافة لازم تكون أرقام')

    if not (-90 <= latitude <= 90):
        raise ValueError('خط العرض لازم يكون بين -90 و 90')

    if not (-180 <= longitude <= 180):
        raise ValueError('خط الطول لازم يكون بين -180 و 180')

    if radius_meters <= 0:
        raise ValueError('نطاق المقر لازم يكون رقم موجب')

    return name.strip(), latitude, longitude, radius_meters


def create_zone(name, latitude, longitude, radius_meters):

    name, latitude, longitude, radius_meters = validate_zone(name, latitude, longitude, radius_meters)

    if Zone.query.filter_by(name=name).first():
        raise ValueError('اسم الفرع ده مستخدم بالفعل')

    zone = Zone(name=name, latitude=latitude, longitude=longitude, radius_meters=radius_meters)
    db.session.add(zone)
    db.session.commit()
    return zone


def update_zone(zone_id, name, latitude, longitude, radius_meters, is_active=True):

    zone = Zone.query.get_or_404(zone_id)
    name, latitude, longitude, radius_meters = validate_zone(name, latitude, longitude, radius_meters)

    existing = Zone.query.filter(Zone.name == name, Zone.id != zone_id).first()
    if existing:
        raise ValueError('اسم الفرع ده مستخدم بالفعل')

    zone.name = name
    zone.latitude = latitude
    zone.longitude = longitude
    zone.radius_meters = radius_meters
    zone.is_active = is_active
    db.session.commit()
    return zone


def delete_zone(zone_id):

    zone = Zone.query.get_or_404(zone_id)

    if zone.users:
        raise ValueError('مينفعش تمسح فرع لسه فيه موظفين متعينين عليه')

    db.session.delete(zone)
    db.session.commit()