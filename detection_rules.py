
def check_calibration(calibration_status):
    status = str(calibration_status or "").strip().upper()
    return status == "CALIBRATED"


def check_physical_reading(temperature, humidity):
    try:
        if temperature is None or humidity is None:
            return False

        temperature = float(temperature)
        humidity = float(humidity)

        return (
            -100 <= temperature <= 100
            and 0 <= humidity <= 100
        )
    except (TypeError, ValueError):
        return False


def check_shipment_dates(departure_time, arrival_time):
    if departure_time is None or arrival_time is None:
        return False

    try:
        return arrival_time >= departure_time
    except TypeError:
        return False


def check_product_policy(shipment_product_id, policy_product_id):
    if not shipment_product_id or not policy_product_id:
        return False

    return (
        str(shipment_product_id).strip()
        == str(policy_product_id).strip()
    )


def reconcile_duration(
    source_readings,
    calculated_duration,
    reading_interval_minutes=5
):
    if not source_readings or calculated_duration is None:
        return False

    try:
        calculated_duration = float(calculated_duration)
        reading_interval_minutes = float(reading_interval_minutes)

        if calculated_duration < 0 or reading_interval_minutes <= 0:
            return False

        ordered_readings = sorted(source_readings)

        if len(ordered_readings) < 2:
            return False

        source_duration = (
            ordered_readings[-1] - ordered_readings[0]
        ).total_seconds() / 60 + reading_interval_minutes

        return calculated_duration >= source_duration

    except (TypeError, ValueError, AttributeError):
        return False


def check_temperature(temperature, minimum, maximum):
    try:
        if temperature is None:
            return "INVALID_READING"

        temperature = float(temperature)
        minimum = float(minimum)
        maximum = float(maximum)

        if temperature < -100 or temperature > 100:
            return "INVALID_READING"

        if temperature > maximum:
            return "HIGH_TEMPERATURE"

        if temperature < minimum:
            return "LOW_TEMPERATURE"

        return "NORMAL"

    except (TypeError, ValueError):
        return "INVALID_READING"


def check_humidity(humidity, minimum, maximum):
    try:
        if humidity is None:
            return "INVALID_READING"

        humidity = float(humidity)
        minimum = float(minimum)
        maximum = float(maximum)

        if humidity < 0 or humidity > 100:
            return "INVALID_READING"

        if humidity > maximum:
            return "HIGH_HUMIDITY"

        if humidity < minimum:
            return "LOW_HUMIDITY"

        return "NORMAL"

    except (TypeError, ValueError):
        return "INVALID_READING"
