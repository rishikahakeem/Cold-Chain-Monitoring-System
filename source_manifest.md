# Cold Chain Monitoring System — Source Manifest

## 1. Project Overview

This manifest lists the main source-code, database, configuration, documentation and frontend files included in the Cold Chain Monitoring System.

## 2. Backend Files

| File | Purpose |
|---|---|
| `app.py` | Flask application, routes, authentication and dashboard functionality |
| `db.py` | MySQL database connection management |
| `generate_data.py` | Generates synthetic shipment, sensor and monitoring data |
| `detect_excursions.py` | Detects temperature, humidity, missing-data and sensor-failure incidents |

## 3. Database Files

| File | Purpose |
|---|---|
| `schema.sql` | Creates the database tables, relationships and initial database structure |
| `ground_truth.csv` | Documents ten expected assessment test scenarios |
| `data_dictionary.md` | Documents database tables, columns, relationships and validation rules |

## 4. Frontend Files

### Templates

The `templates/` directory contains the HTML pages for:

- Dashboard and home page
- Login, signup and password recovery
- Shipment management and shipment details
- Excursion management
- Live monitoring
- Alerts
- Corrective actions
- Reports and report exports
- Navigation

### Static files

| File | Purpose |
|---|---|
| `static/app.js` | Frontend JavaScript functionality |
| `static/style.css` | Application styling |

## 5. Configuration and Dependencies

| File | Purpose |
|---|---|
| `requirements.txt` | Python package dependencies |
| `.gitignore` | Excludes environment files, Python cache and virtual environments |
| `.env` | Local database credentials and application configuration; must not be published |

## 6. Project Documentation

| File | Purpose |
|---|---|
| `README.md` | Installation, database setup, execution instructions and project overview |
| `source_manifest.md` | Inventory of project source and supporting files |

## 7. Data and Testing Notes

- The project uses synthetic data generated with a fixed random seed.
- The test database is `yottaflex_test_db`.
- The original database `yottaflex_db` is kept separate.
- The current dataset contains 1,000 shipments, 300 containers, 300 sensors, 311,824 readings, 3,331 excursions and 240 corrective actions.
- The ground-truth file documents expected outcomes; not every scenario has been implemented and independently tested.
- Live monitoring uses simulated readings and does not connect to physical sensors.

## 8. Security and Submission Notes

- Never publish `.env` or database credentials.
- Do not include passwords, secret keys or private configuration values in the public repository.
- Include the SQL schema, README, data dictionary and ground-truth file in the public repository.

**Project:** Cold Chain Monitoring System  
**Database:** yottaflex_test_db  
**Database Engine:** MySQL / MariaDB  
**Backend:** Python / Flask  
**Frontend:** HTML, CSS and JavaScript