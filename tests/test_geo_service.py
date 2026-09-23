"""
tests/test_geo_service.py — Batch 5

Pure-function tests. No Flask app/context needed to run these.
"""

import pytest
from app.services.geo_service import calculate_distance, is_inside_zone


class FakeZone:
    """Minimal stand-in for the Zone model — only needs .latitude/.longitude/.radius_meters."""

    def __init__(self, latitude, longitude, radius_meters):
        self.latitude = latitude
        self.longitude = longitude
        self.radius_meters = radius_meters


# --- calculate_distance ---------------------------------------------------

def test_zero_distance_same_point():
    assert calculate_distance(30.0444, 31.2357, 30.0444, 31.2357) == pytest.approx(0.0, abs=1e-6)


def test_well_inside_short_distance():
    # Two points ~1km apart in Cairo — sanity-check the order of magnitude.
    d = calculate_distance(30.0444, 31.2357, 30.0534, 31.2357)
    assert 900 < d < 1100


def test_well_outside_far_distance():
    # Cairo vs. Alexandria — roughly 180km apart.
    d = calculate_distance(30.0444, 31.2357, 31.2001, 29.9187)
    assert 150_000 < d < 220_000


def test_antipodal_points_do_not_blow_up():
    # Roughly opposite sides of the Earth — sanity check the formula's upper bound.
    d = calculate_distance(0, 0, 0, 180)
    assert 19_000_000 < d < 20_100_000


def test_invalid_latitude_raises():
    with pytest.raises(ValueError):
        calculate_distance(95, 31.2357, 30.0444, 31.2357)


def test_invalid_longitude_raises():
    with pytest.raises(ValueError):
        calculate_distance(30.0444, 31.2357, 30.0444, 200)


# --- is_inside_zone --------------------------------------------------------

def test_inside_zone_well_within_radius():
    zone = FakeZone(latitude=30.0444, longitude=31.2357, radius_meters=100)
    inside, distance = is_inside_zone(30.0444, 31.2357, zone)
    assert inside is True
    assert distance == pytest.approx(0.0, abs=1e-6)


def test_outside_zone_well_beyond_radius():
    zone = FakeZone(latitude=30.0444, longitude=31.2357, radius_meters=50)
    inside, distance = is_inside_zone(31.2001, 29.9187, zone)
    assert inside is False
    assert distance > 50


def test_exactly_on_boundary_counts_as_inside():
    # Build a point exactly `radius_meters` north of the zone center, then
    # confirm calculate_distance/is_inside_zone agree it's inside (<=, not <).
    zone = FakeZone(latitude=30.0444, longitude=31.2357, radius_meters=100)
    meters_per_degree_lat = 111_320.0
    delta_lat = zone.radius_meters / meters_per_degree_lat
    boundary_lat = zone.latitude + delta_lat

    distance = calculate_distance(boundary_lat, zone.longitude, zone.latitude, zone.longitude)
    inside, reported_distance = is_inside_zone(boundary_lat, zone.longitude, zone)

    assert reported_distance == pytest.approx(distance)
    # Allow a tiny tolerance for the flat-earth approximation used to build the point;
    # the point should land within a meter of the true radius either way.
    assert abs(distance - zone.radius_meters) < 1.0
    assert inside is True


def test_zero_radius_zone_only_inside_at_exact_point():
    zone = FakeZone(latitude=30.0444, longitude=31.2357, radius_meters=0)
    inside_same, _ = is_inside_zone(30.0444, 31.2357, zone)
    inside_off, _ = is_inside_zone(30.0544, 31.2357, zone)
    assert inside_same is True
    assert inside_off is False
