import sqlite3
import os
import json
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emergency_portal.db')

def get_db():
    """Returns a SQLite database connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Initializes the database schema and populates seed data if empty."""
    conn = get_db()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student', 'responder', 'admin')),
            email TEXT,
            phone TEXT,
            hostel_block TEXT,
            room_no TEXT,
            blood_group TEXT,
            medical_notes TEXT,
            emergency_contact_name TEXT,
            emergency_contact_phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Emergencies Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emergencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            emergency_type TEXT NOT NULL,
            severity TEXT DEFAULT 'High',
            description TEXT,
            location_name TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Dispatched', 'On-Scene', 'Resolved', 'Cancelled')),
            responder_id INTEGER,
            responder_notes TEXT,
            eta_minutes INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users(id),
            FOREIGN KEY (responder_id) REFERENCES users(id)
        )
    """)

    # 3. Emergency Contacts Directory
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emergency_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            description TEXT,
            availability TEXT DEFAULT '24/7',
            is_active INTEGER DEFAULT 1
        )
    """)

    # 4. First Aid Guides
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS first_aid_guides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            urgency TEXT DEFAULT 'High',
            symptoms TEXT,
            steps_json TEXT NOT NULL,
            dos_and_donts_json TEXT,
            icon TEXT
        )
    """)

    # 5. Simulated Emergency Notifications / Alerts Log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emergency_id INTEGER,
            recipient_role TEXT,
            recipient_name TEXT,
            recipient_contact TEXT,
            message TEXT,
            channel TEXT DEFAULT 'SMS Simulation',
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (emergency_id) REFERENCES emergencies(id) ON DELETE CASCADE
        )
    """)

    conn.commit()

    # Seed data if no users exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        seed_data(conn)

    conn.close()

def seed_data(conn):
    """Seed initial demo accounts, emergency directory, and medical guides."""
    cursor = conn.cursor()

    # Seed Users
    users_data = [
        # Admin
        ('admin', generate_password_hash('admin123'), 'Dr. Arthur Vance (Chief Proctor)', 'admin', 'proctor@college.edu', '+91 98765 00101', 'Admin Block', 'Office 101', 'A+', 'None', 'Campus Security', '+91 98765 00100'),
        # Responders
        ('security1', generate_password_hash('security123'), 'Quick Response Team (Alpha)', 'responder', 'security@college.edu', '+91 98765 00100', 'Security Main Gate', 'Booth 1', 'O+', 'Trained First Responder & Fire Safety', 'Control Room', '+91 98765 00100'),
        ('medic1', generate_password_hash('medic123'), 'Campus Medical Center Ambulance', 'responder', 'ambulance@college.edu', '+91 98765 00108', 'Health Center', 'Bay 1', 'B+', 'Paramedic / BLS Certified', 'Duty Doctor', '+91 98765 00108'),
        # Students
        ('student1', generate_password_hash('password123'), 'Alex Rivera', 'student', 'alex.rivera@student.college.edu', '+91 98765 43210', 'Hostel Block B (Boys)', 'Room 304', 'O+', 'Mild Asthma (Carries Inhaler)', 'Robert Rivera (Father)', '+91 98765 88990'),
        ('student2', generate_password_hash('password123'), 'Priya Sharma', 'student', 'priya.sharma@student.college.edu', '+91 98765 43211', 'Hostel Block A (Girls)', 'Room 102', 'B+', 'Penicillin Allergy', 'Sunita Sharma (Mother)', '+91 98765 88991'),
    ]

    cursor.executemany("""
        INSERT INTO users (username, password_hash, full_name, role, email, phone, hostel_block, room_no, blood_group, medical_notes, emergency_contact_name, emergency_contact_phone)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, users_data)

    # Seed Emergency Contacts
    contacts_data = [
        ('Medical', 'Campus Emergency Health Center & Ambulance', '+91 98765 00108', '24/7 on-campus ambulance, doctor on call, primary trauma support', '24/7 (Zero Wait)'),
        ('Security', 'Main Campus Security Control Room', '+91 98765 00100', 'Central emergency dispatch, rapid mobile patrol units, gate barriers', '24/7 Immediate'),
        ('Women Safety', 'Anti-Ragging & Women Distress Helpline', '+91 98765 00109', 'Confidential helpline, immediate warden and female officer dispatch', '24/7 Toll-Free'),
        ('Administration', 'Chief Warden & Proctor Office', '+91 98765 00101', 'Hostel discipline, emergency permission, parent coordination', '8:00 AM - 10:00 PM (Emergency 24/7)'),
        ('Mental Health', 'Student Wellness & Psychological Counselor', '+91 98765 00112', 'Stress, panic, anxiety, immediate crisis support & guidance', '9:00 AM - 8:00 PM (Helpline 24/7)'),
        ('Fire & Hazard', 'Campus Fire & Chemical Safety Cell', '+91 98765 00102', 'Laboratory chemical spills, fire alerts, building evacuation', '24/7 On-Call')
    ]

    cursor.executemany("""
        INSERT INTO emergency_contacts (category, name, phone, description, availability)
        VALUES (?, ?, ?, ?, ?)
    """, contacts_data)

    # Seed First Aid Guides
    guides_data = [
        (
            'Cardiopulmonary Resuscitation (CPR)',
            'Medical',
            'Critical',
            'Victim is unconscious, unresponsive, and not breathing normally.',
            json.dumps([
                "Call Campus Ambulance (+91 98765 00108) immediately or press SOS.",
                "Lay the person flat on their back on a firm surface.",
                "Place heel of one hand in the center of their chest, interlock the second hand over it.",
                "Push hard and fast: 100-120 compressions per minute (to the beat of 'Stayin Alive'). Allow chest to rise fully.",
                "Give 2 rescue breaths after every 30 compressions if trained, or continue compression-only CPR until medical help arrives."
            ]),
            json.dumps({
                "dos": ["Start compressions without delay", "Use AED if available on campus", "Keep arms straight and lock elbows"],
                "donts": ["Do not stop compressions unless victim wakes or medics arrive", "Do not give fluids or food"]
            }),
            'fa-heart-pulse'
        ),
        (
            'Severe Bleeding & Open Trauma',
            'Medical',
            'High',
            'Profuse blood flow, deep lacerations, puncture wounds.',
            json.dumps([
                "Ensure your safety and wear gloves if available.",
                "Apply direct, firm pressure on the wound using a clean cloth, sterile pad, or clothing.",
                "Keep pressure continuously for at least 5 to 10 minutes without lifting to check.",
                "Elevate the injured limb above heart level if no fracture is suspected.",
                "If blood soaks through, do NOT remove the first pad; place another pad on top and continue pressing firmly."
            ]),
            json.dumps({
                "dos": ["Press firmly without letting up", "Keep victim calm and lying down to prevent shock"],
                "donts": ["Do NOT pull out deeply embedded objects (glass/metal); stabilize around them", "Do not apply tourniquet unless specifically trained"]
            }),
            'fa-droplet'
        ),
        (
            'Thermal & Chemical Burns',
            'Hazard',
            'High',
            'Redness, blistering, severe pain, chemical contact in lab or hostel.',
            json.dumps([
                "Remove victim from source of heat or chemical safely.",
                "Cool the burn under gentle, running cool tap water for 15-20 minutes (NEVER use ice or ice water).",
                "For chemical spills, brush off dry chemicals first, then flush under campus emergency shower for 15 minutes.",
                "Cover loosely with sterile, non-adherent dressing or clean plastic cling film.",
                "Remove tight rings, belts, or jewelry before swelling begins."
            ]),
            json.dumps({
                "dos": ["Use running cool water immediately", "Keep burned area clean and loosely covered"],
                "donts": ["Never pop blisters", "Never apply butter, toothpaste, or ointments to raw burns", "Do not peel off clothing stuck to the burn"]
            }),
            'fa-fire-flame-curved'
        ),
        (
            'Choking (Conscious Victim)',
            'Medical',
            'Critical',
            'Cannot speak, cough, or breathe; clutching hands to neck (universal choking sign).',
            json.dumps([
                "Ask 'Are you choking?' and encourage them to cough forcefully if they can.",
                "If they cannot cough or speak, stand behind them and slightly to one side.",
                "Give up to 5 sharp back blows between shoulder blades with the heel of your hand.",
                "If back blows fail, give 5 abdominal thrusts (Heimlich maneuver): place fist thumb-side against upper abdomen, grasp with other hand, pull sharply inward and upward.",
                "Repeat cycle of 5 back blows and 5 abdominal thrusts until object is expelled."
            ]),
            json.dumps({
                "dos": ["Act quickly; brain oxygen is cut off", "Alternate back blows with Heimlich thrusts"],
                "donts": ["Do not slap blindly if victim is coughing effectively", "Do not blind sweep their mouth with fingers"]
            }),
            'fa-lungs'
        ),
        (
            'Severe Panic / Anxiety Attack',
            'Mental Health',
            'Medium',
            'Rapid heartbeat, hyperventilation, chest tightness, trembling, feeling of impending doom.',
            json.dumps([
                "Guide the student to a quiet, safe, and ventilated spot.",
                "Reassure them: 'You are safe. This is a panic attack, it will pass in a few minutes.'",
                "Guide 4-4-4 Box Breathing: Inhale slowly through nose for 4 counts, hold for 4 counts, exhale slowly through mouth for 4 counts.",
                "Use 5-4-3-2-1 Grounding: Ask them to name 5 things they see, 4 things they can touch, 3 sounds they hear, 2 scents, and 1 positive thought.",
                "Contact campus student counselor (+91 98765 00112) for quiet debrief."
            ]),
            json.dumps({
                "dos": ["Speak in calm, low, soothing tones", "Stay with them until breathing normalizes"],
                "donts": ["Do not say 'calm down' or dismiss their fears", "Do not crowd around them; give them personal space"]
            }),
            'fa-brain'
        ),
        (
            'Electric Shock & Electrical Hazard',
            'Hazard',
            'Critical',
            'Student in contact with faulty appliance or lab wiring; collapse, burn marks.',
            json.dumps([
                "DO NOT touch the victim with bare hands while they are still in contact with electrical current!",
                "Immediately shut off the main power switch or circuit breaker.",
                "If switch cannot be reached, push victim away using a dry non-conductive object (wooden broom handle, plastic chair).",
                "Once separated from current, check responsiveness and pulse.",
                "If not breathing, start CPR immediately and call Campus Emergency."
            ]),
            json.dumps({
                "dos": ["Disconnect power source first", "Check breathing as soon as current is disconnected"],
                "donts": ["NEVER touch victim with bare hands or wet items if current is on", "Do not move victim unnecessarily if spinal injury suspected"]
            }),
            'fa-bolt'
        )
    ]

    cursor.executemany("""
        INSERT INTO first_aid_guides (title, category, urgency, symptoms, steps_json, dos_and_donts_json, icon)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, guides_data)

    # Seed Sample Emergency Incidents
    # Sample 1: Active medical incident
    cursor.execute("""
        INSERT INTO emergencies (student_id, emergency_type, severity, description, location_name, latitude, longitude, status, responder_id, eta_minutes)
        VALUES (4, 'Medical', 'Critical', 'Student experiencing severe asthma attack, inhaler depleted.', 'Hostel Block B, 3rd Floor, Room 304', 12.9716, 77.5946, 'Dispatched', 3, 4)
    """)
    med_id = cursor.lastrowid

    # Simulated notification for Sample 1
    cursor.execute("""
        INSERT INTO notifications (emergency_id, recipient_role, recipient_name, recipient_contact, message, channel)
        VALUES (?, 'Responder', 'Campus Medical Ambulance', '+91 98765 00108', 'CRITICAL SOS: Medical emergency reported at Hostel Block B, Room 304 by Alex Rivera (O+).', 'SMS Simulation')
    """, (med_id,))
    cursor.execute("""
        INSERT INTO notifications (emergency_id, recipient_role, recipient_name, recipient_contact, message, channel)
        VALUES (?, 'Parent', 'Robert Rivera (Father)', '+91 98765 88990', 'ALERT: Alex Rivera triggered Campus Medical Emergency SOS at Hostel Block B. Responder dispatched (ETA 4 min).', 'SMS Simulation')
    """, (med_id,))

    # Sample 2: Resolved security incident
    cursor.execute("""
        INSERT INTO emergencies (student_id, emergency_type, severity, description, location_name, latitude, longitude, status, responder_id, responder_notes, resolved_at)
        VALUES (5, 'General Security', 'Medium', 'Suspicious person loitering near hostel back gate.', 'Hostel Block A Perimeter', 12.9722, 77.5955, 'Resolved', 2, 'Patrol unit dispatched. Area searched and secured. Guard stationed at perimeter.', datetime('now', '-2 hours'))
    """)

    conn.commit()

if __name__ == '__main__':
    print(f"Initializing database at: {DB_PATH}")
    init_db()
    print("Database schema and seed data created successfully!")
