"""Shared service catalogue and demo assumptions."""

SERVICES: list[dict[str, str]] = [
    {"code": "FUEL", "name": "Fuel", "stream": "SERVICE"},
    {"code": "ITR", "name": "ITR", "stream": "SERVICE"},
    {"code": "MAP", "name": "MAP", "stream": "SERVICE"},
    {"code": "RR", "name": "RR", "stream": "SERVICE"},
    {"code": "TOLL", "name": "Toll", "stream": "SERVICE"},
    {"code": "VIOLATION", "name": "Violation", "stream": "SERVICE"},
    {"code": "COLLISION", "name": "Collision", "stream": "SERVICE"},
    {"code": "INSURANCE", "name": "Insurance", "stream": "SERVICE"},
    {"code": "MILEAGE_LOGGING", "name": "Mileage + Logging", "stream": "SERVICE"},
    {"code": "TELEMATICS", "name": "Telematics", "stream": "SERVICE"},
    {"code": "RENTALS", "name": "Rentals", "stream": "SERVICE"},
    {"code": "MVR_SAFETY", "name": "MVR + Safety", "stream": "SERVICE"},
    {"code": "REMARKETING", "name": "Remarketing", "stream": "SERVICE"},
]

SERVICE_BY_CODE = {item["code"]: item for item in SERVICES}

# These names, rates, and sample terms are synthetic demonstration data only.
