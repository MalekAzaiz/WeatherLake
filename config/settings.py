# config/settings.py

MAX_FETCH_ATTEMPTS = 5
FETCH_DELAY = 5 #seconds

CITIES = {
    # France
    "Paris":     {"lat": 48.8566, "lon": 2.3522},
    "Grenoble":  {"lat": 45.1885, "lon": 5.7245},
    "Lyon":      {"lat": 45.7640, "lon": 4.8357},
    "Marseille": {"lat": 43.2965, "lon": 5.3698},
    "Bordeaux":  {"lat": 44.8378, "lon": -0.5792},
    "Lille":     {"lat": 50.6292, "lon": 3.0573},
    "Nice":      {"lat": 43.7102, "lon": 7.2620},
    # Europe
    "Londres":   {"lat": 51.5074, "lon": -0.1278},
    "Madrid":    {"lat": 40.4168, "lon": -3.7038},
    "Berlin":    {"lat": 52.5200, "lon": 13.4050},
    "Rome":      {"lat": 41.9028, "lon": 12.4964},
    # Mondial
    "New York":  {"lat": 40.7128, "lon": -74.0060},
    "Tokyo":     {"lat": 35.6762, "lon": 139.6503},
    "Dubai":     {"lat": 25.2048, "lon": 55.2708},
    "Sydney":    {"lat": -33.8688, "lon": 151.2093},
}