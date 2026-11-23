
from dataclasses import dataclass
from datetime import datetime, timedelta


SERVICE_DURATION = 30
TURNAROUND_TIME = 15
TIME_SLOT_INTERVAL = SERVICE_DURATION + TURNAROUND_TIME


@dataclass(frozen=True)
class Assignment:
    tanker_id: str
    start_minute: int
    quantity: int
    available_water: int
    location: str

    @property
    def end_minute(self):
        return self.start_minute + SERVICE_DURATION

    def display_time(self):
        hours = self.start_minute // 60
        minutes = self.start_minute % 60
        return f"{hours:02d}:{minutes:02d}"


def parse_time(time_string):
    """Convert a delivery time into minutes from midnight."""

    if not time_string or not time_string.strip():
        return 9 * 60

    formats = ["%H:%M", "%I:%M %p"]

    for fmt in formats:
        try:
            parsed = datetime.strptime(time_string.strip(), fmt)
            return parsed.hour * 60 + parsed.minute
        except ValueError:
            continue

    raise ValueError(
        f"Invalid time '{time_string}'. Use HH:MM or HH:MM AM/PM."
    )


def generate_domains(tankers, requests):
    """
    Generate feasible tanker and time combinations
    for each water request.
    """

    domains = {}

    for request in requests:

        request_id = request[0]
        quantity = int(request[2])
        preferred_time = request[4]
        location = request[5]

        start_time = parse_time(preferred_time)

        domains[request_id] = []

        for tanker in tankers:

            tanker_id = tanker[0]
            capacity = int(tanker[1])
            current_water = int(tanker[2])
            tanker_location = tanker[3]
            available = bool(tanker[4])
            status = tanker[5]

            # Unary constraints
            if not available:
                continue

            if status != "Available":
                continue

            if capacity < quantity:
                continue

            if current_water < quantity:
                continue

            # Generate four candidate delivery slots.
            for offset in range(0, 4):

                delivery_time = (
                    start_time + offset * TIME_SLOT_INTERVAL
                )

                if delivery_time >= 24 * 60:
                    continue

                assignment = Assignment(
                    tanker_id=tanker_id,
                    start_minute=delivery_time,
                    quantity=quantity,
                    available_water=current_water,
                    location=location
                )

                domains[request_id].append(assignment)

    return domains
