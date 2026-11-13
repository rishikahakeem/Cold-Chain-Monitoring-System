# Cold Chain Monitoring System — Data Dictionary

## 1. Overview

This document describes the database structure, field definitions, relationships, units, allowed values and validation rules of the Cold Chain Monitoring System.

**Database name:** `yottaflex_test_db`  
**Database engine:** MySQL / MariaDB

The database contains 10 core business tables:

1. `products`
2. `threshold_policies`
3. `shipments`
4. `containers`
5. `sensors`
6. `route_stops`
7. `sensor_readings`
8. `excursions`
9. `custody_events`
10. `corrective_actions`

The application also uses a separate `users` table for authentication.

Primary keys uniquely identify records. Foreign keys connect related records and maintain referential integrity.

---

## 2. Data Dictionary

### 2.1 Products

**Purpose:** Stores information about products that require temperature and humidity monitoring.

| Column | Data Type | Required | Description / Validation |
|---|---|---|---|
| product_id | VARCHAR(30) | Yes | Primary key; unique product identifier |
| product_name | VARCHAR(100) | Yes | Name of the product |
| category | VARCHAR(50) | No | Product category |
| min_temperature | DECIMAL(5,2) | Yes | Minimum permitted temperature in °C |
| max_temperature | DECIMAL(5,2) | Yes | Maximum permitted temperature in °C |
| min_humidity | DECIMAL(5,2) | No | Minimum permitted humidity percentage |
| max_humidity | DECIMAL(5,2) | No | Maximum permitted humidity percentage |
| created_at | TIMESTAMP | No | Record creation timestamp |

**Validation rules:**

- `product_id` must be unique.
- Minimum temperature must not exceed maximum temperature.
- Minimum humidity must not exceed maximum humidity.
- Humidity thresholds must be between 0 and 100%.
- Product-specific thresholds must be applied when evaluating readings.

### 2.2 Threshold Policies

**Purpose:** Defines the permissible excursion duration for each product, including effective dates.

| Column | Data Type | Required | Description / Validation |
|---|---|---|---|
| policy_id | INT AUTO_INCREMENT | Yes | Primary key |
| product_id | VARCHAR(30) | Yes | Foreign key referencing products |
| max_excursion_minutes | INT | Yes | Maximum permissible excursion duration |
| effective_from | DATE | Yes | Date from which the policy applies |
| effective_to | DATE | No | Policy end date; NULL means no specified end date |

**Validation rules:**

- `product_id` must reference an existing product.
- `max_excursion_minutes` must be positive.
- `effective_to` must not be earlier than `effective_from`.
- Policies for the same product should not have overlapping effective periods.
- The policy effective on the reading date should be used for excursion evaluation.

### 2.3 Shipments

**Purpose:** Stores shipment information, including origin, destination and delivery status.

| Column | Data Type | Required | Description / Validation |
|---|---|---|---|
| shipment_id | VARCHAR(30) | Yes | Primary key; unique shipment identifier |
| product_id | VARCHAR(30) | Yes | Foreign key referencing products |
| origin | VARCHAR(100) | Yes | Shipment starting location |
| destination | VARCHAR(100) | Yes | Shipment destination |
| departure_time | DATETIME | No | Actual or planned departure timestamp |
| expected_arrival | DATETIME | No | Expected delivery timestamp |
| actual_arrival | DATETIME | No | Actual delivery timestamp |
| shipment_status | VARCHAR(30) | No | Shipment lifecycle status |
| created_at | TIMESTAMP | No | Record creation timestamp |

**Validation rules:**

- `shipment_id` must be unique.
- `product_id` must reference an existing product.
- Actual arrival must not be earlier than departure.
- Expected arrival must not be earlier than departure.
- Shipment status must follow documented lifecycle transitions.
- Delayed shipments should retain their expected and actual arrival timestamps.

**Status values currently used in generated data:**

- `DELIVERED`
- `DELAYED`

### 2.4 Containers

**Purpose:** Stores containers assigned to shipments.

| Column | Data Type | Required | Description / Validation |
|---|---|---|---|
| container_id | VARCHAR(30) | Yes | Primary key; unique container identifier |
| shipment_id | VARCHAR(30) | Yes | Foreign key referencing shipments |
| container_type | VARCHAR(50) | No | Type of storage or transport container |
| container_status | VARCHAR(30) | No | Container lifecycle status |

**Validation rules:**

- `container_id` must be unique.
- `shipment_id` must reference an existing shipment.
- Container status must follow documented lifecycle rules.
- A container must be associated with a valid shipment.

**Status currently used in generated data:**

- `ACTIVE`

### 2.5 Sensors

**Purpose:** Stores sensor details and calibration information.

| Column | Data Type | Required | Description / Validation |
|---|---|---|---|
| sensor_id | VARCHAR(50) | Yes | Primary key; unique sensor identifier |
| container_id | VARCHAR(30) | Yes | Foreign key referencing containers |
| sensor_type | VARCHAR(30) | Yes | Sensor measurement type |
| calibration_status | VARCHAR(30) | No | Calibration status |
| last_calibrated | DATETIME | No | Last calibration timestamp |

**Validation rules:**

- `sensor_id` must be unique.
- `container_id` must reference an existing container.
- Sensor type must use documented values.
- Calibration status must use documented values.
- Calibration timestamps must be valid.
- Sensors with expired, failed or invalid calibration should be flagged before their readings are trusted.

**Status currently used in generated data:**

- `CALIBRATED`

**Note:** Calibration failure scenarios are documented as a required future validation case. They are not yet implemented in the current generator.

### 2.6 Route Stops

**Purpose:** Stores planned or actual stops along a shipment route.

| Column | Data Type | Required | Description / Validation |
|---|---|---|---|
| stop_id | INT AUTO_INCREMENT | Yes | Primary key |
| shipment_id | VARCHAR(30) | Yes | Foreign key referencing shipments |
| stop_number | INT | Yes | Stop sequence number within a shipment |
| location | VARCHAR(100) | Yes | Stop location |
| arrival_time | DATETIME | No | Arrival timestamp at the stop |
| departure_time | DATETIME | No | Departure timestamp from the stop |
| stop_status | VARCHAR(30) | No | Stop status |

**Validation rules:**

- `shipment_id` must reference an existing shipment.
- Stop numbers must be positive.
- Stop numbers should be unique within a shipment.
- Departure time must not be earlier than arrival time.
- Route stops must follow the shipment's route sequence.

**Status currently used in generated data:**

- `COMPLETED`

### 2.7 Sensor Readings

**Purpose:** Stores temperature and humidity readings collected during shipment journeys.

| Column | Data Type | Required | Description / Validation |
|---|---|---|---|
| reading_id | VARCHAR(100) | Yes | Primary key; unique reading identifier |
| sensor_id | VARCHAR(50) | Yes | Foreign key referencing sensors |
| shipment_id | VARCHAR(30) | Yes | Foreign key referencing shipments |
| stop_id | INT | No | Optional foreign key referencing route stops |
| temperature | DECIMAL(6,2) | Yes | Recorded temperature in °C |
| humidity | DECIMAL(6,2) | Yes | Recorded humidity percentage |
| reading_time | DATETIME | Yes | Reading timestamp |
| data_status | VARCHAR(30) | No | Reading validity status |

**Validation rules:**

- `reading_id` must be unique.
- Sensor and shipment IDs must reference existing records.
- If provided, `stop_id` must reference an existing route stop.
- Humidity must be between 0 and 100% for physically valid readings.
- Temperature must be checked against documented physical plausibility limits.
- Readings must be associated with the correct sensor, container and shipment.
- Missing readings and sensor failures must not automatically be treated as safe conditions.
- Readings should be checked for duplicate timestamps and unexpected intervals.
- Readings must be evaluated against the applicable product thresholds.

**Status values currently used:**

- `VALID`
- `SENSOR_FAILURE`

**Indexes documented:**

- `idx_reading_time` on `reading_time`.
- `idx_shipment_time` on `shipment_id` and `reading_time`.

**Physical validation note:**

The current dataset was checked for temperature values below -100°C or above 100°C and humidity values below 0% or above 100%. No such values were found. Explicit invalid-measurement injection and detection still require implementation.

### 2.8 Excursions

**Purpose:** Stores detected temperature, humidity and sensor-related incidents.

| Column | Data Type | Required | Description / Validation |
|---|---|---|---|
| excursion_id | VARCHAR(30) | Yes | Primary key; unique excursion identifier |
| shipment_id | VARCHAR(30) | Yes | Foreign key referencing shipments |
| sensor_id | VARCHAR(50) | Yes | Foreign key referencing sensors |
| excursion_type | VARCHAR(30) | Yes | Incident type |
| start_time | DATETIME | Yes | Incident start timestamp |
| end_time | DATETIME | No | Incident end timestamp |
| duration_minutes | DECIMAL(10,2) | No | Calculated incident duration in minutes |
| maximum_temperature | DECIMAL(6,2) | No | Maximum recorded temperature during the incident |
| maximum_humidity | DECIMAL(6,2) | No | Maximum recorded humidity during the incident |
| excursion_status | VARCHAR(30) | No | Incident status |
| severity | VARCHAR(20) | No | Incident severity |

**Incident types supported by the detection logic:**

- `HIGH_TEMPERATURE`
- `LOW_TEMPERATURE`
- `HIGH_HUMIDITY`
- `LOW_HUMIDITY`
- `MISSING_DATA`
- `SENSOR_FAILURE`

**Severity values used by the detection logic:**

- `CRITICAL`
- `HIGH`
- `MEDIUM`
- `LOW`

**Validation rules:**

- `excursion_id` must be unique.
- Shipment and sensor IDs must reference existing records.
- End time must not be earlier than start time.
- Duration must be calculated from incident timestamps and documented business rules.
- Severity must follow documented excursion-duration rules.
- Incident types must use documented values.
- Maximum measurement values must be derived from source readings.
- Missing data incidents should be distinguishable from temperature and humidity excursions.

**Status currently used:**

- `OPEN`

### 2.9 Custody Events

**Purpose:** Maintains a traceable history of shipment handling and custody changes.

| Column | Data Type | Required | Description / Validation |
|---|---|---|---|
| event_id | INT AUTO_INCREMENT | Yes | Primary key |
| shipment_id | VARCHAR(30) | Yes | Foreign key referencing shipments |
| event_type | VARCHAR(50) | Yes | Type of custody or handling event |
| responsible_person | VARCHAR(100) | No | Person responsible for the event |
| event_location | VARCHAR(100) | No | Location where the event occurred |
| event_time | DATETIME | Yes | Timestamp of the event |
| remarks | TEXT | No | Additional event details |

**Validation rules:**

- `shipment_id` must reference an existing shipment.
- Event time must be valid.
- Events must be retained as historical records rather than overwritten.
- Event ordering should be checked against shipment lifecycle timestamps.
- Custody events must be associated with the correct shipment.

**Event types currently generated:**

- `PICKUP`
- `DELIVERY`

**Index documented:**

- `idx_custody_time` on `shipment_id` and `event_time`.

### 2.10 Corrective Actions

**Purpose:** Stores actions taken to investigate and resolve detected excursions.

| Column | Data Type | Required | Description / Validation |
|---|---|---|---|
| action_id | INT AUTO_INCREMENT | Yes | Primary key |
| excursion_id | VARCHAR(30) | No | Optional foreign key referencing excursions |
| shipment_id | VARCHAR(30) | Yes | Foreign key referencing shipments |
| action_description | TEXT | Yes | Description of the corrective action |
| assigned_to | VARCHAR(100) | No | Person responsible for the action |
| action_status | VARCHAR(30) | No | Corrective action status |
| created_at | TIMESTAMP | No | Action creation timestamp |
| completed_at | DATETIME | No | Action completion timestamp |

**Validation rules:**

- `shipment_id` must reference an existing shipment.
- If supplied, `excursion_id` must reference an existing excursion.
- Action status must follow valid lifecycle transitions.
- Completed actions should have a valid completion timestamp.
- Completion time must not be earlier than creation time.
- Corrective actions should be traceable to the incident and shipment that caused them.

**Status values currently used:**

- `PENDING`
- `COMPLETED`

---

## 3. Entity Relationships

| Parent Table | Child Table | Relationship |
|---|---|---|
| products | threshold_policies | One-to-many |
| products | shipments | One-to-many |
| shipments | containers | One-to-many |
| containers | sensors | One-to-many |
| shipments | route_stops | One-to-many |
| sensors | sensor_readings | One-to-many |
| shipments | sensor_readings | One-to-many |
| route_stops | sensor_readings | One-to-many; optional reading reference |
| shipments | excursions | One-to-many |
| sensors | excursions | One-to-many |
| shipments | custody_events | One-to-many |
| excursions | corrective_actions | One-to-many; optional excursion reference |
| shipments | corrective_actions | One-to-many |

**Relationship integrity rules:**

- Every primary key must uniquely identify a record.
- Foreign keys must reference existing parent records.
- A sensor reading must belong to the shipment associated with its sensor's container.
- A route stop associated with a reading must belong to the same shipment as that reading.
- An excursion must belong to the correct sensor and shipment.
- A corrective action must reference the correct shipment and, when applicable, excursion.
- Historical records should be preserved for traceability.

---

## 4. Units of Measurement

| Measurement | Unit |
|---|---|
| Temperature | Degrees Celsius (°C) |
| Humidity | Percentage (%) |
| Excursion duration | Minutes |
| Effective policy dates | Calendar date |
| Event timestamps | Date and time |
| Reading timestamps | Date and time |

---

## 5. ID and Naming Conventions

The current data generator uses the following ID formats:

| Entity | ID format | Example |
|---|---|---|
| Shipment | `SHP-####` | `SHP-0001` |
| Container | `CONT-####` | `CONT-0001` |
| Sensor | `SENSOR-####` | `SENSOR-0001` |
| Sensor Reading | Sensor ID + timestamp | `SENSOR-0001-202601011200` |
| Excursion | `EXC-######` | `EXC-000001` |
| Route Stop | Auto-increment integer | `1` |
| Threshold Policy | Auto-increment integer | `1` |
| Custody Event | Auto-increment integer | `1` |
| Corrective Action | Auto-increment integer | `1` |

IDs must be unique, stable and consistently referenced across related tables.

**Assessment naming note:** The assessment provides alternative examples such as `SHP-2026-000001`, `CNT-000001` and `SNS-CNT-000001-TEMP`. The current generator uses the formats documented above rather than those exact examples.

---

## 6. Business Validation Rules

The application should validate the following conditions:

1. Product minimum thresholds must not exceed maximum thresholds.
2. Shipment arrival must not occur before departure.
3. Route stop departure must not occur before arrival.
4. Sensor readings must be linked to valid sensors and shipments.
5. Temperature and humidity readings must be compared against applicable product thresholds.
6. Threshold policies must be selected according to their effective dates.
7. Excursion duration must be calculated from source readings and documented rules.
8. Sensor failures and missing reading intervals must be identified as exceptions.
9. Physically invalid measurements must be flagged rather than treated as normal readings.
10. Sensor calibration status must be checked before readings are trusted.
11. Corrective action status changes must follow valid lifecycle transitions.
12. Custody events must preserve shipment handling history.
13. Derived incident results must be traceable to their source readings and applicable rules.
14. Invalid date ordering and incorrect product-threshold associations must be flagged.
15. Duplicate IDs and invalid foreign-key references must be prevented.

---

## 7. Ground-Truth and Edge-Case Scenarios

The separate `ground_truth.csv` file documents expected outcomes for ten assessment scenarios.

| Case ID | Scenario | Expected decision |
|---|---|---|
| GT-001 | Normal condition | NO_EXCURSION |
| GT-002 | Brief high temperature | DETECT_EXCURSION |
| GT-003 | Prolonged high temperature | DETECT_EXCURSION |
| GT-004 | Low temperature | DETECT_EXCURSION |
| GT-005 | High humidity | DETECT_EXCURSION |
| GT-006 | Sensor dropout | FLAG_MISSING_DATA |
| GT-007 | Invalid physical reading | FLAG_INVALID_DATA |
| GT-008 | Delivery before departure | REJECT_RECORD |
| GT-009 | Wrong-product threshold | FLAG_POLICY_ERROR |
| GT-010 | Excursion duration undercount | FLAG_CALCULATION_ERROR |

**Validation note:**

These cases define expected outcomes, not proof that every scenario has been implemented or passed.

The current implementation supports normal conditions, temperature and humidity excursions, missing intervals and sensor failures. Explicit handling and independent testing of all remaining edge cases are still required.

---

## 8. Database Validation and Verification

The current test database has been checked using SQL validation queries.

### 8.1 Dataset counts

| Table / Entity | Verified records |
|---|---:|
| Shipments | 1,000 |
| Containers | 300 |
| Sensors | 300 |
| Route Stops | 3,000 |
| Sensor Readings | 311,824 |
| Excursions | 3,331 |
| Corrective Actions | 240 |

### 8.2 Relationship validation

| Validation | Result |
|---|---|
| Sensor readings without sensors | 0 |
| Sensor readings without shipments | 0 |
| Sensors without containers | 0 |
| Sensors without shipments | 0 |
| Corrective actions without excursions | 0 |
| Corrective actions without shipments | 0 |
| Excursions without sensors | 0 |
| Excursions without shipments | 0 |

### 8.3 Excursion duration validation

| Validation | Result |
|---|---:|
| Total excursions | 3,331 |
| Missing durations | 0 |
| Invalid durations | 0 |
| Minimum duration | 5 minutes |
| Maximum duration | 65 minutes |

### 8.4 Physical measurement validation

The existing dataset was checked for:

- Temperature below -100°C or above 100°C.
- Humidity below 0% or above 100%.

No readings violating these screening limits were found in the current dataset.

**Important:** These checks establish the condition of the current dataset. They do not prove that all possible invalid inputs are rejected by the application.

---

## 9. Database Notes and Limitations

- The SQL schema defines the ten core business tables.
- The application also uses a `users` table for authentication.
- The `users` table must be included in the reproducible setup instructions for a fresh installation.
- Some business rules require application-level validation and are not necessarily enforced by SQL constraints.
- Status columns are stored as VARCHAR fields; allowed values should be validated by the application.
- The current dataset uses synthetic data generated with a fixed random seed.
- The live monitoring page displays simulated readings; it is not connected to physical sensor hardware.
- The current generator creates route delays, controlled temperature and humidity excursions, random sensor failures and missing reading intervals.
- Calibration failure injection and the remaining ground-truth edge cases still require implementation and validation.
- The current test database is named `yottaflex_test_db`; the original `yottaflex_db` database is kept separate.
- Database verification results reflect the test database at the time of testing.

---

## 10. Reproducibility and Submission Requirements

The project uses a fixed random seed:

```python
random.seed(42)
```

This supports repeatable random-number generation.

The assessment additionally requests:

1. Regenerate the dataset twice using the same seed.
2. Compare row counts and checksums.
3. Document the generator command and required dependencies.
4. Include the SQL schema and data dictionary.
5. Include `ground_truth.csv`.
6. Provide a source manifest and validation summary.
7. Export relevant seed data in CSV, JSON or SQL format.
8. Publish the project in a public GitHub repository.
9. Include a README explaining installation, database setup and execution.

**Note:** A fixed random seed alone does not prove that complete database regeneration is reproducible. A separate controlled comparison is still required.

---

**Document:** Data Dictionary  
**Database:** yottaflex_test_db  
**Database Engine:** MySQL / MariaDB  
**Project:** Cold Chain Monitoring System  
**Version:** Updated assessment documentation