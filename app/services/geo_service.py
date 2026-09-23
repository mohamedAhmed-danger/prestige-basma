"""
geo_service.py — Batch 5

Pure GPS math. No Flask, no SQLAlchemy session usage, no I/O — these
functions must be callable and testable with zero app context.
"""

import math


def calculate_distance(lat1, lng1, lat2, lng2):
    """Great-circle distance between two lat/lng points, in meters (Haversine).

    Raises ValueError if any coordinate is out of its valid range.
    """
    for lat in (lat1, lat2):
        if not (-90 <= lat <= 90):
            raise ValueError('خط العرض لازم يكون بين -90 و 90')
    for lng in (lng1, lng2):
        if not (-180 <= lng <= 180):
            raise ValueError('خط الطول لازم يكون بين -180 و 180')

    EARTH_RADIUS_METERS = 6371000.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_METERS * c


def is_inside_zone(user_lat, user_lng, zone):
    """Whether (user_lat, user_lng) falls within `zone`'s radius.

    Returns (inside: bool, distance: float). Exactly-on-the-boundary
    (distance == radius) counts as inside — <=, not <.
    """
    distance = calculate_distance(user_lat, user_lng, zone.latitude, zone.longitude)
    inside = distance <= zone.radius_meters
    return inside, distance
