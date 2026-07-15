import math

import pytest

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    def to_rad(d: float) -> float:
        return d * math.pi / 180

    dlat = to_rad(lat2 - lat1)
    dlon = to_rad(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(to_rad(lat1)) * math.cos(to_rad(lat2)) * math.sin(dlon / 2) ** 2
    return EARTH_RADIUS_KM * 2 * math.asin(math.sqrt(a))


def test_haversine_paris_london() -> None:
    km = haversine_km(48.8566, 2.3522, 51.5074, -0.1278)
    assert 340 < km < 360


def test_haversine_zero_distance_same_point() -> None:
    assert haversine_km(-34.8941, -56.1527, -34.8941, -56.1527) == pytest.approx(0.0, abs=1e-6)
