
import csv
import io
import os
import secrets
import random
from datetime import datetime
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    request,
    Response,
    redirect,
    flash,
    session,
)
from werkzeug.security import generate_password_hash, check_password_hash

from db import get_connection

# =========================================================
# APPLICATION CONFIGURATION
# =========================================================

load_dotenv()

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError(
        "SECRET_KEY is missing. Add SECRET_KEY=<random-secret> to your .env file."
    )

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get(
        "COOKIE_SECURE", "false"
    ).lower() == "true",
    PERMANENT_SESSION_LIFETIME=60 * 60 * 8,
)
csrf = CSRFProtect(app)

VALID_SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

VALID_EXCURSION_TYPES = [
    "HIGH_TEMPERATURE",
    "LOW_TEMPERATURE",
    "HIGH_HUMIDITY",
    "SENSOR_FAILURE",
]


# =========================================================
# LOGIN PROTECTION
# =========================================================

@app.before_request
def require_login():

    # These pages are accessible without logging in.
    allowed_routes = [
        "home",
        "login",
        "signup",
        "forgot_password",
        "static",
    ]

    if request.endpoint in allowed_routes:
        return None

    # All other pages require login.
    if not session.get("user_id"):
        return redirect("/login")


# =========================================================
# 1. HOME PAGE
# =========================================================

@app.route("/")
def home():
    return render_template("home.html")


# =========================================================
# 2. MAIN DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    selected_severity = request.args.get("severity", "").upper()
    selected_type = request.args.get("excursion_type", "").upper()
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    if selected_severity not in VALID_SEVERITIES:
        selected_severity = ""

    if selected_type not in VALID_EXCURSION_TYPES:
        selected_type = ""

    conditions = []
    params = []

    if selected_severity:
        conditions.append("severity = %s")
        params.append(selected_severity)

    if selected_type:
        conditions.append("excursion_type = %s")
        params.append(selected_type)

    if start_date:
        conditions.append("DATE(start_time) >= %s")
        params.append(start_date)

    if end_date:
        conditions.append("DATE(start_time) <= %s")
        params.append(end_date)

    where_clause = (
        " WHERE " + " AND ".join(conditions)
        if conditions else ""
    )

    connection = get_connection()
    print("DASHBOARD DATABASE:", connection.database)

    if connection is None:
        return "Database connection failed.", 500

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("SELECT COUNT(*) AS total FROM shipments")
        total_shipments = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM containers")
        total_containers = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM sensors")
        total_sensors = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM sensor_readings")
        total_readings = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT COUNT(*) AS total FROM excursions" + where_clause,
            tuple(params),
        )
        total_excursions = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT COUNT(*) AS total FROM excursions"
            + where_clause
            + (" AND " if where_clause else " WHERE ")
            + "severity = 'CRITICAL'",
            tuple(params),
        )
        critical_excursions = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT COUNT(*) AS total FROM excursions"
            + where_clause
            + (" AND " if where_clause else " WHERE ")
            + "severity = 'HIGH'",
            tuple(params),
        )
        high_excursions = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM corrective_actions
            WHERE action_status = 'PENDING'
        """)
        pending_actions = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT excursion_type, COUNT(*) AS total
            FROM excursions
        """ + where_clause + """
            GROUP BY excursion_type
            ORDER BY total DESC
        """, tuple(params))
        excursion_types = cursor.fetchall()

        cursor.execute("""
            SELECT severity, COUNT(*) AS total
            FROM excursions
        """ + where_clause + """
            GROUP BY severity
            ORDER BY FIELD(
                severity, 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
            )
        """, tuple(params))
        severity_stats = cursor.fetchall()

        reading_conditions = ["data_status = 'VALID'"]
        reading_params = []

        if start_date:
            reading_conditions.append("DATE(reading_time) >= %s")
            reading_params.append(start_date)

        if end_date:
            reading_conditions.append("DATE(reading_time) <= %s")
            reading_params.append(end_date)

        reading_where = " WHERE " + " AND ".join(reading_conditions)

        cursor.execute("""
            SELECT
                DATE(reading_time) AS reading_date,
                ROUND(AVG(temperature), 2) AS avg_temperature,
                ROUND(AVG(humidity), 2) AS avg_humidity
            FROM sensor_readings
        """ + reading_where + """
            GROUP BY DATE(reading_time)
            ORDER BY reading_date DESC
            LIMIT 14
        """, tuple(reading_params))

        daily_readings = cursor.fetchall()
        daily_readings.reverse()

        cursor.execute("""
            SELECT
                excursion_id,
                shipment_id,
                sensor_id,
                excursion_type,
                severity,
                start_time,
                duration_minutes
            FROM excursions
        """ + where_clause + """
            ORDER BY start_time DESC
            LIMIT 10
        """, tuple(params))
        recent_excursions = cursor.fetchall()

        cursor.execute("""
            SELECT
                excursion_id,
                shipment_id,
                action_description,
                assigned_to,
                action_status
            FROM corrective_actions
            ORDER BY excursion_id DESC
            LIMIT 10
        """)
        recent_actions = cursor.fetchall()

        return render_template(
            "dashboard.html",
            total_shipments=total_shipments,
            total_containers=total_containers,
            total_sensors=total_sensors,
            total_readings=total_readings,
            total_excursions=total_excursions,
            critical_excursions=critical_excursions,
            high_excursions=high_excursions,
            pending_actions=pending_actions,
            excursion_types=excursion_types,
            severity_stats=severity_stats,
            daily_readings=daily_readings,
            recent_excursions=recent_excursions,
            recent_actions=recent_actions,
            selected_severity=selected_severity,
            selected_type=selected_type,
            start_date=start_date,
            end_date=end_date,
        )

    except Exception as error:
        app.logger.exception("Dashboard error")
        return f"Dashboard error: {error}", 500

    finally:
        cursor.close()
        connection.close()


# =========================================================
# 3. SHIPMENT DETAILS PAGE
# =========================================================

@app.route("/shipment/<shipment_id>")
def shipment_details(shipment_id):

    connection = get_connection()

    if connection is None:
        return "Database connection failed.", 500

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                s.shipment_id,
                s.product_id,
                p.product_name,
                s.origin,
                s.destination,
                s.departure_time,
                s.expected_arrival,
                s.actual_arrival,
                s.shipment_status
            FROM shipments s
            LEFT JOIN products p ON s.product_id = p.product_id
            WHERE s.shipment_id = %s
        """, (shipment_id,))

        shipment = cursor.fetchone()

        if shipment is None:
            return render_template(
                "shipments.html",
                shipment=None,
                containers=[],
                latest_readings=[],
                route_stops=[],
                excursions=[],
                corrective_actions=[],
                custody_events=[],
            ), 404

        cursor.execute("""
            SELECT
                c.container_id,
                c.container_type,
                c.container_status,
                se.sensor_id,
                se.sensor_type,
                se.calibration_status
            FROM containers c
            LEFT JOIN sensors se ON c.container_id = se.container_id
            WHERE c.shipment_id = %s
            ORDER BY c.container_id
        """, (shipment_id,))
        containers = cursor.fetchall()

        cursor.execute("""
            SELECT
                sr.sensor_id,
                sr.temperature,
                sr.humidity,
                sr.reading_time,
                sr.data_status
            FROM sensor_readings sr
            WHERE sr.shipment_id = %s
            ORDER BY sr.reading_time DESC
            LIMIT 10
        """, (shipment_id,))
        latest_readings = cursor.fetchall()

        cursor.execute("""
            SELECT
                stop_number,
                location,
                arrival_time,
                departure_time,
                stop_status
            FROM route_stops
            WHERE shipment_id = %s
            ORDER BY stop_number
        """, (shipment_id,))
        route_stops = cursor.fetchall()

        cursor.execute("""
            SELECT
                excursion_id,
                sensor_id,
                excursion_type,
                severity,
                start_time,
                duration_minutes,
                excursion_status
            FROM excursions
            WHERE shipment_id = %s
            ORDER BY start_time DESC
        """, (shipment_id,))
        excursions = cursor.fetchall()

        cursor.execute("""
            SELECT
                action_id,
                action_description,
                assigned_to,
                action_status,
                created_at
            FROM corrective_actions
            WHERE shipment_id = %s
            ORDER BY created_at DESC
        """, (shipment_id,))
        corrective_actions = cursor.fetchall()

        cursor.execute("""
            SELECT
                event_id,
                event_type,
                responsible_person,
                event_location,
                event_time,
                remarks
            FROM custody_events
            WHERE shipment_id = %s
            ORDER BY event_time DESC
        """, (shipment_id,))
        custody_events = cursor.fetchall()

        return render_template(
            "shipments.html",
            shipment=shipment,
            containers=containers,
            latest_readings=latest_readings,
            route_stops=route_stops,
            excursions=excursions,
            corrective_actions=corrective_actions,
            custody_events=custody_events,
        )

    except Exception as error:
        app.logger.exception("Shipment details error")
        return f"Shipment details error: {error}", 500

    finally:
        cursor.close()
        connection.close()


# =========================================================
# 4. SHIPMENT MANAGEMENT LIST PAGE
# =========================================================

@app.route("/shipments")
def shipments_list():

    connection = get_connection()

    if connection is None:
        return "Database connection failed.", 500

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT s.*, p.product_name
            FROM shipments s
            LEFT JOIN products p ON s.product_id = p.product_id
            ORDER BY s.shipment_id
        """)

        shipments = cursor.fetchall()

        return render_template(
            "shipments_list.html",
            shipments=shipments
        )

    except Exception as error:
        app.logger.exception("Shipment list error")
        return f"Shipment list error: {error}", 500

    finally:
        cursor.close()
        connection.close()


# =========================================================
# 5. EXCURSION MANAGEMENT PAGE
# =========================================================

@app.route("/excursions")
def excursions():

    selected_severity = request.args.get("severity", "").upper()
    selected_type = request.args.get("excursion_type", "").upper()

    if selected_severity not in VALID_SEVERITIES:
        selected_severity = ""

    if selected_type not in VALID_EXCURSION_TYPES:
        selected_type = ""

    connection = get_connection()

    if connection is None:
        return "Database connection failed.", 500

    cursor = connection.cursor(dictionary=True)

    try:

        query = """
            SELECT
                excursion_id,
                shipment_id,
                sensor_id,
                excursion_type,
                severity,
                start_time,
                duration_minutes,
                maximum_temperature
            FROM excursions
            WHERE 1=1
        """

        params = []

        if selected_severity:
            query += " AND severity = %s"
            params.append(selected_severity)

        if selected_type:
            query += " AND excursion_type = %s"
            params.append(selected_type)

        query += " ORDER BY start_time DESC"

        cursor.execute(query, tuple(params))
        excursion_records = cursor.fetchall()

        return render_template(
            "excursions.html",
            excursions=excursion_records,
            severities=VALID_SEVERITIES,
            excursion_types=VALID_EXCURSION_TYPES,
            selected_severity=selected_severity,
            selected_type=selected_type,
        )

    except Exception as error:
        app.logger.exception("Excursion management error")
        return f"Excursion management error: {error}", 500

    finally:
        cursor.close()
        connection.close()


# =========================================================
# 6. LIVE MONITORING PAGE
# =========================================================

@app.route("/live-monitoring")
def live_monitoring():

    connection = get_connection()

    if connection is None:
        return "Database connection failed.", 500

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("SELECT COUNT(*) AS total FROM sensors")
        total_sensors = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT
                sr.sensor_id,
                sr.shipment_id,
                p.product_name,
                sr.temperature,
                sr.humidity,
                sr.reading_time,
                sr.data_status,
                p.min_temperature,
                p.max_temperature,
                p.min_humidity,
                p.max_humidity
            FROM sensor_readings sr
            INNER JOIN (
                SELECT sensor_id, MAX(reading_time) AS latest_time
                FROM sensor_readings
                GROUP BY sensor_id
            ) latest
                ON sr.sensor_id = latest.sensor_id
                AND sr.reading_time = latest.latest_time
            INNER JOIN shipments s ON sr.shipment_id = s.shipment_id
            INNER JOIN products p ON s.product_id = p.product_id
            ORDER BY sr.reading_time DESC
        """)

        readings = cursor.fetchall()

        normal_count = 0
        abnormal_count = 0

        for row in readings:

            if row["data_status"] != "VALID":

                row["temperature_status"] = "INVALID"
                row["humidity_status"] = "INVALID"
                row["overall_status"] = "INVALID"

            else:

                temperature = row["temperature"]
                humidity = row["humidity"]

                if (
                    temperature is None
                    or temperature < row["min_temperature"]
                    or temperature > row["max_temperature"]
                ):
                    row["temperature_status"] = "CRITICAL"
                else:
                    row["temperature_status"] = "NORMAL"

                if (
                    humidity is None
                    or humidity < row["min_humidity"]
                    or humidity > row["max_humidity"]
                ):
                    row["humidity_status"] = "CRITICAL"
                else:
                    row["humidity_status"] = "NORMAL"

                if (
                    row["temperature_status"] == "CRITICAL"
                    or row["humidity_status"] == "CRITICAL"
                ):
                    row["overall_status"] = "CRITICAL"
                else:
                    row["overall_status"] = "NORMAL"

            if row["overall_status"] == "NORMAL":
                normal_count += 1
            else:
                abnormal_count += 1

        return render_template(
            "live_monitoring.html",
            total_sensors=total_sensors,
            normal_count=normal_count,
            abnormal_count=abnormal_count,
            readings=readings,
        )

    except Exception as error:
        app.logger.exception("Live monitoring error")
        return f"Live monitoring error: {error}", 500

    finally:
        cursor.close()
        connection.close()


# =========================================================
# 7. ALERT MANAGEMENT PAGE
# =========================================================

@app.route("/alerts")
def alerts():

    connection = get_connection()

    if connection is None:
        return "Database connection failed.", 500

    cursor = connection.cursor(dictionary=True)

    try:

        selected_severity = request.args.get("severity", "").upper()

        if selected_severity not in ["", "CRITICAL", "HIGH"]:
            selected_severity = ""

        query = """
            SELECT
                excursion_id,
                shipment_id,
                sensor_id,
                excursion_type,
                severity,
                start_time,
                duration_minutes
            FROM excursions
            WHERE severity IN ('CRITICAL', 'HIGH')
        """

        params = []

        if selected_severity:
            query += " AND severity = %s"
            params.append(selected_severity)

        query += " ORDER BY start_time DESC"

        cursor.execute(query, tuple(params))
        alerts_list = cursor.fetchall()

        cursor.execute("""
            SELECT
                COUNT(*) AS total_alerts,
                SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END)
                    AS critical_alerts,
                SUM(CASE WHEN severity = 'HIGH' THEN 1 ELSE 0 END)
                    AS high_alerts
            FROM excursions
            WHERE severity IN ('CRITICAL', 'HIGH')
        """)

        summary = cursor.fetchone()

        return render_template(
            "alerts.html",
            alerts=alerts_list,
            total_alerts=summary["total_alerts"] or 0,
            critical_alerts=summary["critical_alerts"] or 0,
            high_alerts=summary["high_alerts"] or 0,
            selected_severity=selected_severity,
        )

    except Exception as error:
        app.logger.exception("Alerts page error")
        return f"Alerts page error: {error}", 500

    finally:
        cursor.close()
        connection.close()


# =========================================================
# 8. CORRECTIVE ACTIONS MANAGEMENT PAGE
# =========================================================

@app.route("/corrective-actions")
def corrective_actions():

    connection = get_connection()

    if connection is None:
        return "Database connection failed.", 500

    cursor = connection.cursor(dictionary=True)

    try:

        selected_status = request.args.get("status", "").upper()

        if selected_status not in ["", "PENDING", "COMPLETED"]:
            selected_status = ""

        query = """
            SELECT
                action_id,
                excursion_id,
                shipment_id,
                action_description,
                assigned_to,
                created_at,
                action_status
            FROM corrective_actions
            WHERE 1=1
        """

        params = []

        if selected_status:
            query += " AND action_status = %s"
            params.append(selected_status)

        query += " ORDER BY created_at DESC"

        cursor.execute(query, tuple(params))
        actions = cursor.fetchall()

        cursor.execute("""
            SELECT
                COUNT(*) AS total_actions,
                SUM(CASE WHEN action_status = 'PENDING' THEN 1 ELSE 0 END)
                    AS pending_actions,
                SUM(CASE WHEN action_status = 'COMPLETED' THEN 1 ELSE 0 END)
                    AS completed_actions
            FROM corrective_actions
        """)

        summary = cursor.fetchone()

        return render_template(
            "corrective_actions.html",
            actions=actions,
            total_actions=summary["total_actions"] or 0,
            pending_actions=summary["pending_actions"] or 0,
            completed_actions=summary["completed_actions"] or 0,
            selected_status=selected_status,
        )

    except Exception as error:
        app.logger.exception("Corrective actions error")
        return f"Corrective actions error: {error}", 500

    finally:
        cursor.close()
        connection.close()


# =========================================================
# 9. UPDATE CORRECTIVE ACTION STATUS
# =========================================================

@app.route(
    "/corrective-actions/update/<int:action_id>",
    methods=["POST"]
)
def update_corrective_action(action_id):

    new_status = request.form.get("action_status", "").upper()

    if new_status not in ["PENDING", "COMPLETED"]:
        return "Invalid corrective action status.", 400

    connection = get_connection()

    if connection is None:
        return "Database connection failed.", 500

    cursor = connection.cursor()

    try:

        cursor.execute("""
            UPDATE corrective_actions
            SET action_status = %s
            WHERE action_id = %s
        """, (new_status, action_id))

        if cursor.rowcount == 0:
            connection.rollback()
            return "Corrective action not found.", 404

        connection.commit()

        flash("Corrective action status updated successfully.")

        return redirect("/corrective-actions")

    except Exception as error:
        connection.rollback()
        app.logger.exception("Corrective action update error")
        return f"Corrective action update error: {error}", 500

    finally:
        cursor.close()
        connection.close()


# =========================================================
# 10. REPORTS & ANALYTICS PAGE
# =========================================================

@app.route("/reports")
def reports():
    return render_template("reports.html")


# =========================================================
# 11. SHIPMENT REPORT
# =========================================================

@app.route("/reports/shipments")
def shipment_report():

    connection = get_connection()

    if connection is None:
        return "Database connection failed.", 500

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT s.*, p.product_name
            FROM shipments s
            LEFT JOIN products p ON s.product_id = p.product_id
            ORDER BY s.shipment_id
        """)

        shipments = cursor.fetchall()

        return render_template(
            "shipment_report.html",
            shipments=shipments
        )

    except Exception as error:
        app.logger.exception("Shipment report error")
        return f"Shipment report error: {error}", 500

    finally:
        cursor.close()
        connection.close()


# =========================================================
# 12. EXCURSION REPORT
# =========================================================

@app.route("/reports/excursions")
def excursion_report():

    connection = get_connection()

    if connection is None:
        return "Database connection failed.", 500

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                excursion_id,
                shipment_id,
                sensor_id,
                excursion_type,
                severity,
                start_time,
                duration_minutes,
                maximum_temperature
            FROM excursions
            ORDER BY start_time DESC
        """)

        excursions = cursor.fetchall()

        return render_template(
            "excursion_report.html",
            excursions=excursions
        )

    except Exception as error:
        app.logger.exception("Excursion report error")
        return f"Excursion report error: {error}", 500

    finally:
        cursor.close()
        connection.close()


# =========================================================
# 13. CORRECTIVE ACTIONS REPORT
# =========================================================

@app.route("/reports/corrective-actions")
def corrective_actions_report():

    connection = get_connection()

    if connection is None:
        return "Database connection failed.", 500

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                action_id,
                excursion_id,
                shipment_id,
                action_description,
                assigned_to,
                created_at,
                action_status
            FROM corrective_actions
            ORDER BY created_at DESC
        """)

        actions = cursor.fetchall()

        return render_template(
            "corrective_actions_report.html",
            actions=actions,
        )

    except Exception as error:
        app.logger.exception("Corrective actions report error")
        return f"Corrective actions report error: {error}", 500

    finally:
        cursor.close()
        connection.close()


# =========================================================
# 14. SENSOR READINGS REPORT
# =========================================================

@app.route("/reports/readings")
def sensor_readings_report():

    connection = get_connection()

    if connection is None:
        return "Database connection failed.", 500

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                sr.sensor_id,
                c.shipment_id,
                sr.temperature,
                sr.humidity,
                sr.reading_time,
                sr.data_status
            FROM sensor_readings sr
            LEFT JOIN sensors s ON sr.sensor_id = s.sensor_id
            LEFT JOIN containers c ON s.container_id = c.container_id
            ORDER BY sr.reading_time DESC
            LIMIT 500
        """)

        readings = cursor.fetchall()

        cursor.execute("""
            SELECT COUNT(*) AS total_readings
            FROM sensor_readings
        """)

        total = cursor.fetchone()

        return render_template(
            "sensor_readings_report.html",
            readings=readings,
            total_readings=total["total_readings"] or 0,
        )

    except Exception as error:
        app.logger.exception("Sensor readings report error")
        return f"Sensor readings report error: {error}", 500

    finally:
        cursor.close()
        connection.close()



# =========================================================
# 15. CUSTOM DATE RANGE REPORT
# =========================================================

@app.route("/reports/custom")
def custom_report():

    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    if not start_date or not end_date:
        return "Please select both start date and end date.", 400

    if start_date > end_date:
        return "Start date cannot be after end date.", 400

    connection = get_connection()

    if connection is None:
        return "Database connection failed.", 500

    cursor = connection.cursor(dictionary=True)

    try:

        # 1. Total excursions
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM excursions
            WHERE DATE(start_time) BETWEEN %s AND %s
        """, (start_date, end_date))

        excursion_count = cursor.fetchone()["total"] or 0

        # 2. Total corrective actions
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM corrective_actions
            WHERE DATE(created_at) BETWEEN %s AND %s
        """, (start_date, end_date))

        action_count = cursor.fetchone()["total"] or 0

        # 3. Total sensor readings
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM sensor_readings
            WHERE DATE(reading_time) BETWEEN %s AND %s
        """, (start_date, end_date))

        reading_count = cursor.fetchone()["total"] or 0

        # 4. Excursion records
        # Show temperature only for temperature incidents
        # Show humidity only for humidity incidents
        cursor.execute("""
            SELECT
                excursion_id,
                shipment_id,
                sensor_id,
                excursion_type,
                severity,
                start_time,
                duration_minutes,

                CASE
                    WHEN excursion_type IN (
                        'HIGH_HUMIDITY',
                        'LOW_HUMIDITY'
                    )
                    THEN NULL
                    ELSE maximum_temperature
                END AS maximum_temperature,

                CASE
                    WHEN excursion_type IN (
                        'HIGH_HUMIDITY',
                        'LOW_HUMIDITY'
                    )
                    THEN maximum_humidity
                    ELSE NULL
                END AS maximum_humidity

            FROM excursions
            WHERE DATE(start_time) BETWEEN %s AND %s
            ORDER BY start_time DESC
            LIMIT 100
        """, (start_date, end_date))

        excursions = cursor.fetchall()

        # 5. Corrective action records
        cursor.execute("""
            SELECT
                action_id,
                excursion_id,
                shipment_id,
                action_description,
                assigned_to,
                created_at,
                action_status
            FROM corrective_actions
            WHERE DATE(created_at) BETWEEN %s AND %s
            ORDER BY created_at DESC
            LIMIT 100
        """, (start_date, end_date))

        actions = cursor.fetchall()

        # 6. Sensor reading records
        cursor.execute("""
            SELECT
                sr.sensor_id,
                c.shipment_id,
                sr.temperature,
                sr.humidity,
                sr.reading_time,
                sr.data_status
            FROM sensor_readings sr
            LEFT JOIN sensors s
                ON sr.sensor_id = s.sensor_id
            LEFT JOIN containers c
                ON s.container_id = c.container_id
            WHERE DATE(sr.reading_time) BETWEEN %s AND %s
            ORDER BY sr.reading_time DESC
            LIMIT 100
        """, (start_date, end_date))

        readings = cursor.fetchall()

        # 7. Display custom report
        return render_template(
            "custom_report.html",
            start_date=start_date,
            end_date=end_date,
            excursion_count=excursion_count,
            action_count=action_count,
            reading_count=reading_count,
            excursions=excursions,
            actions=actions,
            readings=readings,
        )

    except Exception as error:
        app.logger.exception("Custom report error")
        return f"Custom report error: {error}", 500

    finally:
        cursor.close()
        connection.close()

# =========================================================
# 16. COMMON CSV EXPORT FUNCTION
# =========================================================

def export_csv_report(query, filename, params=()):

    connection = get_connection()

    if connection is None:
        return "Database connection failed.", 500

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(query, params)

        rows = cursor.fetchall()
        columns = cursor.column_names

        output = io.StringIO()

        writer = csv.DictWriter(
            output,
            fieldnames=columns,
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(rows)

        response = Response(
            "\ufeff" + output.getvalue(),
            mimetype="text/csv; charset=utf-8",
        )

        response.headers["Content-Disposition"] = (
            f'attachment; filename="{filename}"'
        )

        return response

    except Exception as error:
        app.logger.exception("CSV export error")
        return f"CSV export error: {error}", 500

    finally:
        cursor.close()
        connection.close()


# =========================================================
# 17. SHIPMENT CSV EXPORT
# =========================================================

@app.route("/export/shipments")
def export_shipments():

    query = """
        SELECT s.*, p.product_name
        FROM shipments s
        LEFT JOIN products p ON s.product_id = p.product_id
        ORDER BY s.shipment_id
    """

    return export_csv_report(
        query,
        "shipment_report.csv"
    )


# =========================================================
# 18. EXCURSION CSV EXPORT
# =========================================================

@app.route("/export/excursions")
def export_excursions():

    query = """
        SELECT
            excursion_id,
            shipment_id,
            sensor_id,
            excursion_type,
            severity,
            start_time,
            duration_minutes,
            maximum_temperature
        FROM excursions
        ORDER BY start_time DESC
    """

    return export_csv_report(
        query,
        "excursion_report.csv"
    )


# =========================================================
# 19. CORRECTIVE ACTIONS CSV EXPORT
# =========================================================

@app.route("/export/corrective-actions")
def export_corrective_actions():

    query = """
        SELECT
            action_id,
            excursion_id,
            shipment_id,
            action_description,
            assigned_to,
            created_at,
            action_status
        FROM corrective_actions
        ORDER BY created_at DESC
    """

    return export_csv_report(
        query,
        "corrective_actions_report.csv"
    )


# =========================================================
# 20. SENSOR READINGS CSV EXPORT
# =========================================================

@app.route("/export/readings")
def export_readings():

    query = """
        SELECT
            sr.sensor_id,
            c.shipment_id,
            sr.temperature,
            sr.humidity,
            sr.reading_time,
            sr.data_status
        FROM sensor_readings sr
        LEFT JOIN sensors s ON sr.sensor_id = s.sensor_id
        LEFT JOIN containers c ON s.container_id = c.container_id
        ORDER BY sr.reading_time DESC
    """

    return export_csv_report(
        query,
        "sensor_readings_report.csv"
    )


# =========================================================
# 21. CUSTOM DATE RANGE CSV EXPORT
# =========================================================

@app.route("/export/custom")
def export_custom_report():

    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    if not start_date or not end_date:
        return "Please select both dates.", 400

    if start_date > end_date:
        return "Start date cannot be after end date.", 400

    connection = get_connection()

    if connection is None:
        return "Database connection failed.", 500

    cursor = connection.cursor(dictionary=True)

    try:

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "Record Type",
            "ID",
            "Excursion ID",
            "Shipment ID",
            "Sensor ID",
            "Type",
            "Severity",
            "Temperature",
            "Humidity",
            "Duration Minutes",
            "Description",
            "Assigned To",
            "Status",
            "Date",
            "Data Status",
        ])

        # Export excursions.
        cursor.execute("""
            SELECT
                excursion_id,
                shipment_id,
                sensor_id,
                excursion_type,
                severity,
                start_time,
                duration_minutes,
                maximum_temperature
            FROM excursions
            WHERE DATE(start_time) BETWEEN %s AND %s
            ORDER BY start_time DESC
        """, (start_date, end_date))

        for row in cursor.fetchall():

            writer.writerow([
                "EXCURSION",
                row["excursion_id"],
                row["excursion_id"],
                row["shipment_id"],
                row["sensor_id"],
                row["excursion_type"],
                row["severity"],
                row["maximum_temperature"],
                "",
                row["duration_minutes"],
                "",
                "",
                "",
                row["start_time"],
                "",
            ])

        # Export corrective actions.
        cursor.execute("""
            SELECT
                action_id,
                excursion_id,
                shipment_id,
                action_description,
                assigned_to,
                action_status,
                created_at
            FROM corrective_actions
            WHERE DATE(created_at) BETWEEN %s AND %s
            ORDER BY created_at DESC
        """, (start_date, end_date))

        for row in cursor.fetchall():

            writer.writerow([
                "CORRECTIVE ACTION",
                row["action_id"],
                row["excursion_id"],
                row["shipment_id"],
                "",
                "",
                "",
                "",
                "",
                "",
                row["action_description"],
                row["assigned_to"],
                row["action_status"],
                row["created_at"],
                "",
            ])

        # Export sensor readings.
        cursor.execute("""
            SELECT
                sr.sensor_id,
                c.shipment_id,
                sr.temperature,
                sr.humidity,
                sr.reading_time,
                sr.data_status
            FROM sensor_readings sr
            LEFT JOIN sensors s ON sr.sensor_id = s.sensor_id
            LEFT JOIN containers c ON s.container_id = c.container_id
            WHERE DATE(sr.reading_time) BETWEEN %s AND %s
            ORDER BY sr.reading_time DESC
        """, (start_date, end_date))

        for row in cursor.fetchall():

            writer.writerow([
                "SENSOR READING",
                row["sensor_id"],
                "",
                row["shipment_id"],
                row["sensor_id"],
                "",
                "",
                row["temperature"],
                row["humidity"],
                "",
                "",
                "",
                "",
                row["reading_time"],
                row["data_status"],
            ])

        response = Response(
            "\ufeff" + output.getvalue(),
            mimetype="text/csv; charset=utf-8",
        )

        response.headers["Content-Disposition"] = (
            'attachment; filename="custom_full_report.csv"'
        )

        return response

    except Exception as error:
        app.logger.exception("Custom CSV export error")
        return f"Custom CSV export error: {error}", 500

    finally:
        cursor.close()
        connection.close()


# =========================================================
# 22. LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        connection = get_connection()

        if connection is None:
            flash("Database connection failed.")
            return redirect("/login")

        cursor = connection.cursor()

        try:

            cursor.execute("""
                SELECT user_id, name, password
                FROM users
                WHERE email = %s
            """, (email,))

            user = cursor.fetchone()

            if user and check_password_hash(user[2], password):

                session.clear()
                session.permanent = True
                session["user_id"] = user[0]
                session["user_name"] = user[1]

                # IMPORTANT: After login, open the Dashboard.
                return redirect("/dashboard")

            flash("Invalid email or password.")
            return redirect("/login")

        except Exception:
            app.logger.exception("Login error")
            flash("Login failed. Please try again.")
            return redirect("/login")

        finally:
            cursor.close()
            connection.close()

    # If already logged in, open Dashboard.
    if session.get("user_id"):
        return redirect("/dashboard")

    return render_template("login.html")


# =========================================================
# 23. FORGOT PASSWORD
# =========================================================

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        recovery_code = request.form.get("recovery_code", "").strip()
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not all([
            email,
            recovery_code,
            new_password,
            confirm_password
        ]):
            flash("Please fill in all fields.")
            return redirect("/forgot-password")

        if len(new_password) < 8:
            flash("Password must contain at least 8 characters.")
            return redirect("/forgot-password")

        if new_password != confirm_password:
            flash("Passwords do not match.")
            return redirect("/forgot-password")

        connection = get_connection()

        if connection is None:
            flash("Database connection failed.")
            return redirect("/forgot-password")

        cursor = connection.cursor()

        try:

            cursor.execute("""
                SELECT user_id, recovery_code
                FROM users
                WHERE email = %s
            """, (email,))

            user = cursor.fetchone()

            if not user or not user[1]:
                flash("Invalid email or recovery code.")
                return redirect("/forgot-password")

            if not check_password_hash(user[1], recovery_code):
                flash("Invalid email or recovery code.")
                return redirect("/forgot-password")

            hashed_password = generate_password_hash(new_password)

            cursor.execute("""
                UPDATE users
                SET password = %s,
                    recovery_code = NULL
                WHERE user_id = %s
            """, (hashed_password, user[0]))

            connection.commit()

            flash("Password reset successfully. Please login.")

            return redirect("/login")

        except Exception:
            connection.rollback()
            app.logger.exception("Password reset error")
            flash("Password reset failed. Please try again.")
            return redirect("/forgot-password")

        finally:
            cursor.close()
            connection.close()

    return render_template("forgot_password.html")


# =========================================================
# 24. SIGNUP
# =========================================================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Please fill in all fields.")
            return redirect("/signup")

        if len(password) < 8:
            flash("Password must contain at least 8 characters.")
            return redirect("/signup")

        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect("/signup")

        connection = get_connection()

        if connection is None:
            flash("Database connection failed.")
            return redirect("/signup")

        cursor = connection.cursor()

        try:

            cursor.execute(
                "SELECT user_id FROM users WHERE email = %s",
                (email,),
            )

            if cursor.fetchone():
                flash("Email is already registered.")
                return redirect("/signup")

            hashed_password = generate_password_hash(password)

            recovery_code = secrets.token_urlsafe(16)

            hashed_recovery_code = generate_password_hash(recovery_code)

            cursor.execute("""
                INSERT INTO users (
                    name,
                    email,
                    password,
                    recovery_code
                )
                VALUES (%s, %s, %s, %s)
            """, (
                name,
                email,
                hashed_password,
                hashed_recovery_code
            ))

            connection.commit()

            flash("Account created successfully!")
            flash("YOUR RECOVERY CODE: " + recovery_code)
            flash("Save this code safely. It will not be shown again.")

            return redirect("/login")

        except Exception:
            connection.rollback()
            app.logger.exception("Signup error")
            flash("Signup failed. Please try again.")
            return redirect("/signup")

        finally:
            cursor.close()
            connection.close()

    return render_template("signup.html")


# =========================================================
# 25. LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================================================
# RUN FLASK APPLICATION
# =========================================================

if __name__ == "__main__":

    debug_mode = os.environ.get(
        "FLASK_DEBUG", "false"
    ).lower() == "true"

    app.run(debug=debug_mode)
