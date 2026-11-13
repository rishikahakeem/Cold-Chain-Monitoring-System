# Cold Chain Monitoring System

## Project Overview

The Cold Chain Monitoring System is a web-based application designed to monitor temperature and humidity throughout storage and transportation journeys.

The system helps identify environmental excursions, monitor shipments, track sensor readings, manage corrective actions and maintain traceability of cold-chain operations.

It provides a centralized dashboard for monitoring shipment conditions and reviewing operational exceptions.

## Problem Statement

Temperature-sensitive products require controlled environmental conditions during storage and transportation.

Unexpected temperature or humidity changes can affect product quality and safety. This system helps identify such conditions, record excursions and support corrective actions through a centralized monitoring platform.

## Key Features

- **Dashboard:** Overview of shipments, sensor readings, excursions and corrective actions.
- **Shipment Management:** View shipment information and shipment details.
- **Excursion Management:** Identify and review temperature and humidity excursions.
- **Live Monitoring:** View simulated live sensor readings and environmental conditions.
- **Alert Management:** Review high-severity and critical exceptions.
- **Corrective Actions:** Track and update corrective action statuses.
- **Reports and Analytics:** Generate shipment, excursion, corrective action and sensor reading reports.
- **Custom Reports:** Generate reports using a selected date range.
- **CSV Export:** Export report data for further analysis.
- **PDF Export:** Print reports or save them as PDF through the browser.
- **User Authentication:** Signup, login, logout and password recovery.
- **Database Integration:** Store and retrieve operational records using MySQL.

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript, Bootstrap |
| Database | MySQL / MariaDB |
| Authentication | Werkzeug Password Hashing |
| Security | Flask-WTF CSRF Protection |
| Data Processing | Python |
| Development Environment | Visual Studio Code |

## Database Entities

The system uses the following database entities:

1. Products
2. Threshold Policies
3. Shipments
4. Containers
5. Sensors
6. Route Stops
7. Sensor Readings
8. Excursions
9. Custody Events
10. Corrective Actions
11. Users

The Users table is maintained separately for application authentication.

## Dataset Information

The current generated development dataset contains:

- **1,000** shipments
- **300** containers
- **300** sensors
- **311,824** sensor readings
- **3,331** detected excursions
- **240** corrective actions

These figures represent the current development dataset and may change if the dataset is regenerated.

## Project Structure

```text
YottaFlex_Cold_Chain/
│
├── app.py
├── db.py
├── generate_data.py
├── detect_excursions.py
├── schema.sql
├── requirements.txt
├── README.md
├── data_dictionary.md
├── ground_truth.csv
├── .gitignore
│
├── templates/
│   ├── alerts.html
│   ├── corrective_actions.html
│   ├── corrective_actions_report.html
│   ├── custom_report.html
│   ├── dashboard.html
│   ├── excursion_report.html
│   ├── excursions.html
│   ├── forgot_password.html
│   ├── home.html
│   ├── index.html
│   ├── live_monitoring.html
│   ├── login.html
│   ├── navbar.html
│   ├── reports.html
│   ├── sensor_readings_report.html
│   ├── shipment_report.html
│   ├── shipments_list.html
│   ├── shipments.html
│   └── signup.html
│
└── static/
    ├── app.js
    └── style.css
```

The `.env` file must be created locally and should not be uploaded to GitHub.

## Installation and Setup

### Prerequisites

- Python 3
- MySQL or XAMPP MariaDB
- Visual Studio Code
- Git

### 1. Clone the Repository

```bash
git clone YOUR_PUBLIC_GITHUB_REPOSITORY_URL
cd YottaFlex_Cold_Chain
```

Replace the repository URL with the actual public GitHub repository URL.

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root directory.

Configure the following values according to your local MySQL setup:

```env
DB_HOST=127.0.0.1
DB_PORT=3307
DB_USER=root
DB_PASSWORD=
DB_NAME=yottaflex_test_db

SECRET_KEY=replace-with-a-unique-secret-key
FLASK_DEBUG=false
```

Use your own database credentials and a unique secret key.

Do not upload your actual `.env` file, database passwords or secret keys to GitHub.

### 4. Set Up the Database

1. Start MySQL using XAMPP.
2. Open phpMyAdmin.
3. Import the provided `schema.sql` file.
4. The schema creates and uses the database `yottaflex_test_db`.
5. Ensure the database connection settings match your `.env` configuration.

**Additional database setup for a fresh installation:**

The application uses a `maximum_humidity` column in the excursions table. Add it after importing the schema:

```sql
ALTER TABLE excursions
ADD COLUMN maximum_humidity DECIMAL(6,2) NULL
AFTER maximum_temperature;
```

The application also requires a Users table for authentication. Create it using:

```sql
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    recovery_code VARCHAR(255) NULL
);
```

### 5. Run the Application

```bash
python app.py
```

Open the application in your browser:

http://127.0.0.1:5000

Create an account and log in to access the monitoring dashboard.

## Data Generation and Excursion Detection

The project includes scripts for generating synthetic shipment data and detecting excursions.

Generate the dataset:

```bash
python generate_data.py
```

Run excursion detection:

```bash
python detect_excursions.py
```

Run these scripts during initial data setup or when intentionally creating a new dataset.

Avoid running them repeatedly against an existing populated database. Follow the duplicate-data safeguards in the scripts.

## Live Monitoring

The Live Monitoring module displays simulated sensor readings for the available sensors.

The displayed readings are generated by the application for demonstration purposes. They are not received from physical IoT hardware.

The simulation does not insert new readings into the database.

## Security

- Passwords are stored using secure password hashing.
- CSRF protection is implemented for protected forms.
- Session-based login protection is implemented.
- Database credentials and application secrets are configured through environment variables.
- The `.env` file is excluded from version control.

## Reports and Outputs

The application provides:

- Shipment Reports
- Excursion Reports
- Corrective Action Reports
- Sensor Reading Reports
- Custom Date-Range Reports
- CSV Data Exports
- Browser Print / Save as PDF

## Documentation and Validation

The repository includes:

- `schema.sql` – Database schema and sample product and threshold policy records.
- `data_dictionary.md` – Description of database tables and their fields.
- `ground_truth.csv` – Reference scenarios and expected detection outcomes.

## Future Enhancements

- IoT hardware sensor integration
- Email and automated notifications
- Shipment route visualization
- Predictive analytics
- Advanced sensor health monitoring

## Project Objective

To provide a centralized cold-chain monitoring solution that improves environmental visibility, identifies excursions, maintains traceability and supports timely corrective actions.

---

**Project:** Cold Chain Monitoring System  
**Backend:** Python Flask  
**Database:** MySQL / MariaDB  
