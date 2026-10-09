# 🚨 College Student Emergency Assistance Portal

An end-to-end, responsive emergency management and panic assistance web application tailored for college campuses. It equips university students, security dispatchers, hostel wardens, and medical personnel with immediate communication, live GPS incident mapping, student medical dossiers, automated emergency alerts, and verified first-aid protocols.

---

## 📌 Project Overview & Objectives

In large collegiate campuses, medical emergencies, ragging/harassment incidents, lab chemical hazards, and hostel distress require immediate response. Traditional phone calls are often delayed, and callers struggle to convey precise locations or critical medical context (like blood group, asthma, or drug allergies).

### Key Objectives
- **Instant SOS Panic Trigger**: One-click broadcast with a 4-second safety countdown to prevent false alarms.
- **Role-Based Access Control (RBAC)**: Distinct, authenticated dashboards for **Students**, **Campus Security/Responders**, and **Chief Proctor/Administrators**.
- **Real-Time Incident Triage & Live Radar**: Dispatchers view open incidents ordered by severity (`Critical`, `High`, `Medium`), update response stages (`Pending` ➔ `Dispatched` ➔ `On-Scene` ➔ `Resolved`), and set live ETAs.
- **Live Interactive Campus Map**: Powered by Leaflet.js and OpenStreetMap to display real-time emergency beacons.
- **Medical Dossier Integration**: Responders instantly access the victim's blood group, existing medical conditions, and parent/guardian contacts.
- **Automated SMS Simulation Feed**: Logs dispatched alerts sent to guardians and campus security units.
- **Built-in First Aid & Safety Protocols**: Searchable, categorized emergency guides (CPR, severe bleeding, burns, choking, panic attacks, electric shock) with Dos & Don'ts.
- **Campus Speed-Dial Directory**: Quick-access helpline directory for ambulances, security desks, women's grievance cell, and mental health counselors.

---

## 🛠️ Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| **Backend Framework** | **Python Flask 3.0+** | Lightweight, modular, fast routing, and minimal overhead |
| **Database** | **SQLite 3** | Serverless, zero-config, self-contained file (`emergency_portal.db`) |
| **Frontend UI** | **HTML5 + Bootstrap 5.3** | High-contrast, mobile-first responsive layout with accessible alerts |
| **Icons & Typography** | **FontAwesome 6.5** | High-visibility emergency and medical iconography |
| **Maps & Geolocation** | **Leaflet.js + HTML5 Geolocation API** | Open-source interactive campus mapping and GPS coordinate retrieval |
| **Audio Synthesizer** | **HTML5 Web Audio API** | Real-time siren tone modulation without requiring external MP3 files |
| **Security & Auth** | **Werkzeug Security** | Salted SHA-256 password hashing and session token verification |

---

## 📂 Project Directory Structure

```text
MINI PROJECT PYTHON/
├── app.py                     # Main Flask web application & REST API controllers
├── database.py                # Database connection, SQLite schema, and seed data generator
├── emergency_portal.db        # SQLite database (auto-generated)
├── requirements.txt           # Python dependency specifications
├── test_portal.py             # Automated unit & integration test suite (7 tests)
├── run.bat                    # 1-Click Windows execution script with auto-browser launch
├── README.md                  # Comprehensive project report & viva preparation
├── static/
│   ├── css/
│   │   └── style.css          # Emergency theme, radar pulse animations, and custom UI
│   └── js/
│       └── main.js            # Web Audio siren, Geolocation, SOS triggers & live polling
└── templates/
    ├── base.html              # Core navigation layout, emergency speed-dial banner & modals
    ├── index.html             # Public emergency landing page with 1-touch SOS trigger
    ├── login.html             # Multi-role authentication with 1-click demo filler buttons
    ├── register.html          # Student safety onboarding (residence, medical & guardian data)
    ├── student_dashboard.html # Student console with live pipeline status tracker & SOS
    ├── responder_dashboard.html# Control room radar with interactive map and triage actions
    ├── admin_dashboard.html   # Chief Proctor overview, analytics metrics & helpline manager
    ├── first_aid.html         # Searchable life-saving protocols and emergency steps
    ├── campus_directory.html  # Campus emergency speed-dial phone directory
    └── profile.html           # Profile & medical dossier editor
```

---

## 🔑 Pre-Configured Demo Accounts

For instant evaluation, the database comes pre-seeded with test accounts across all roles:

| Role | Username | Password | Full Name / Description |
|---|---|---|---|
| **Student** | `student1` | `password123` | Alex Rivera (Hostel Block B, Room 304, Blood: O+) |
| **Student** | `student2` | `password123` | Priya Sharma (Hostel Block A, Room 102, Blood: B+) |
| **Responder** | `security1` | `security123` | Campus Quick Response Team (QRT Alpha) |
| **Responder** | `medic1` | `medic123` | Campus Medical Center Ambulance Team |
| **Admin** | `admin` | `admin123` | Dr. Arthur Vance (Chief Proctor & Warden) |

> *Tip: On the Login screen, click any of the 1-Click Demo Credential buttons to log in instantly without typing!*

---

## 🚀 How to Run the Project

### Method 1: One-Click Windows Batch Runner (Recommended)
1. Navigate to the project directory: `c:\Users\Lappy\OneDrive\Desktop\MINI PROJECT PYTHON`.
2. Double-click **`run.bat`**.
3. The script will automatically check Python, install required packages, verify database seed data, start the Flask server, and launch `http://127.0.0.1:5000` in your default browser.

### Method 2: Manual Terminal Execution
```bash
# 1. Open PowerShell or Command Prompt in this folder
cd "c:\Users\Lappy\OneDrive\Desktop\MINI PROJECT PYTHON"

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Initialize the database and sample records
python database.py

# 4. Start the application
python app.py
```
Open **`http://127.0.0.1:5000`** in your browser.

---

## 🧪 Running Automated Tests

Run the full automated test suite covering authentication, SOS creation, dispatch APIs, and data integrity:

```bash
python test_portal.py
```

Expected output:
```text
.......
----------------------------------------------------------------------
Ran 7 tests in 0.606s

OK
```

---

## 🌐 Key Application Workflows

1. **Triggering an Emergency SOS (Student Flow)**:
   - Student logs in or taps **SOS** from the homepage.
   - Selects category (e.g., *Medical Emergency*, *Ragging*, *Fire*).
   - The system retrieves GPS location coordinates and pre-fills the student's room.
   - A 4-second countdown modal appears with sound; upon confirmation, the emergency is logged as `Pending`.
   - Simulated SMS notifications are sent to the campus ambulance and parent contact.
   - The student's dashboard displays a visual pipeline: `Reported` ➔ `Dispatched` ➔ `On Scene` ➔ `Resolved`.

2. **Triage & Dispatch (Responder Flow)**:
   - Security guards or medics log in to the **Responder Control Room**.
   - An audible siren sounds when an emergency is active.
   - The interactive Leaflet campus map displays an animated emergency beacon at the incident coordinates.
   - Responders click **"Dispatch Unit"**, assign an estimated arrival time (ETA), and click **"Dossier"** to view the student's medical conditions (e.g., asthma, blood group).
   - Once at the scene, they click **"Mark On-Scene"** and subsequently **"Resolve Incident"** with resolution remarks.

3. **Administration & Analytics (Chief Proctor Flow)**:
   - Chief Proctor logs in to the **Admin Dashboard**.
   - Views analytical KPIs: Total Incidents, Active Emergencies, Resolved Cases, and Registered Students.
   - Analyzes incidents categorized by frequency (Medical vs. Security vs. Ragging).
   - Reviews the comprehensive incident audit trail.
   - Adds or edits official campus emergency helpline numbers.

---

## 🎓 Viva & Presentation Q&A Reference

**Q1: Why did you choose SQLite over MySQL for this mini project?**
> *Answer:* SQLite is serverless, zero-configuration, and stores the entire database within a single local file (`emergency_portal.db`). This makes the application 100% portable for project submission, evaluation, and demonstration without requiring the evaluator to install and configure an external MySQL server daemon.

**Q2: How does the application capture location without native mobile apps?**
> *Answer:* We leverage the W3C standard **HTML5 Geolocation API** (`navigator.geolocation.getCurrentPosition`), which accesses browser GPS coordinates. If GPS is unavailable or blocked, the system falls back seamlessly to the student's registered campus residence block and room number.

**Q3: How are passwords protected in the database?**
> *Answer:* Passwords are never stored in plaintext. We utilize Werkzeug's `generate_password_hash()` which generates a secure, salted SHA-256 hash. When a user logs in, `check_password_hash()` verifies the input against the stored hash.

**Q4: How does the siren sound function without external media files?**
> *Answer:* We implemented an oscillator using the browser's native **Web Audio API** (`AudioContext`). It synthesizes a dual-frequency sawtooth wave modulating between 650 Hz and 980 Hz, mimicking an emergency siren without relying on external `.mp3` files that could fail to load.

**Q5: How does the portal maintain real-time updates for responders?**
> *Answer:* The frontend runs asynchronous AJAX polling every 6 seconds against the `/api/emergencies/active` endpoint. When a new incident is detected, the dashboard automatically updates the incident counter, updates the Leaflet map pins, and triggers the audio siren.
