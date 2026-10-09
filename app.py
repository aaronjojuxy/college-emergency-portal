import os
import json
import sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_db, init_db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'college_emergency_portal_super_secret_key_2026')

# Initialize DB on start if needed
init_db()

# --- Helpers & Decorators ---

def get_current_user():
    """Returns the current logged-in user record or None."""
    if 'user_id' not in session:
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    conn.close()
    return user

def login_required(roles=None):
    """Decorator to enforce login and optional role permissions."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this portal section.', 'warning')
                return redirect(url_for('login', next=request.path))
            user_role = session.get('role')
            if roles and user_role not in roles:
                flash('Unauthorized access: You do not have permission to view that page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.context_processor
def inject_globals():
    """Injects user and system status into all templates."""
    current_user = get_current_user()
    conn = get_db()
    active_count = conn.execute("SELECT COUNT(*) FROM emergencies WHERE status IN ('Pending', 'Dispatched', 'On-Scene')").fetchone()[0]
    conn.close()
    return {
        'current_user': current_user,
        'active_emergencies_count': active_count,
        'now': datetime.now()
    }

# --- General Routes ---

@app.route('/')
def index():
    """Public Emergency Landing Page with Quick Actions."""
    conn = get_db()
    emergency_contacts = conn.execute("SELECT * FROM emergency_contacts WHERE is_active = 1 LIMIT 6").fetchall()
    top_guides = conn.execute("SELECT * FROM first_aid_guides LIMIT 4").fetchall()
    conn.close()
    return render_template('index.html', emergency_contacts=emergency_contacts, top_guides=top_guides)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Unified Login Route for Students, Responders, and Admins."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Please enter both username and password.', 'warning')
            return render_template('login.html')

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            flash(f"Welcome back, {user['full_name']}! Logged in as {user['role'].capitalize()}.", 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard'))
        else:
            flash('Invalid username or password. Please verify and try again.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Student Registration with campus details."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        hostel_block = request.form.get('hostel_block', '').strip()
        room_no = request.form.get('room_no', '').strip()
        blood_group = request.form.get('blood_group', '').strip()
        medical_notes = request.form.get('medical_notes', '').strip()
        emergency_contact_name = request.form.get('emergency_contact_name', '').strip()
        emergency_contact_phone = request.form.get('emergency_contact_phone', '').strip()

        if not username or not full_name or not password or not phone:
            flash('Please fill in all required fields marked with *.', 'warning')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        conn = get_db()
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            conn.close()
            flash('Username is already taken. Please choose another username.', 'warning')
            return render_template('register.html')

        password_hash = generate_password_hash(password)
        conn.execute("""
            INSERT INTO users (username, password_hash, full_name, role, email, phone, hostel_block, room_no, blood_group, medical_notes, emergency_contact_name, emergency_contact_phone)
            VALUES (?, ?, ?, 'student', ?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, password_hash, full_name, email, phone, hostel_block, room_no, blood_group, medical_notes, emergency_contact_name, emergency_contact_phone))
        conn.commit()
        conn.close()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    """Logout current user."""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required()
def dashboard():
    """Role-based redirection."""
    role = session.get('role')
    if role == 'student':
        return redirect(url_for('student_dashboard'))
    elif role == 'responder':
        return redirect(url_for('responder_dashboard'))
    elif role == 'admin':
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('index'))

# --- Student Dashboard ---

@app.route('/student/dashboard')
@login_required(roles=['student'])
def student_dashboard():
    """Student Emergency Central: SOS trigger, active tracking, past history."""
    conn = get_db()
    student_id = session['user_id']
    
    # Active emergency for this student
    active_emergency = conn.execute("""
        SELECT e.*, r.full_name as responder_name, r.phone as responder_phone
        FROM emergencies e
        LEFT JOIN users r ON e.responder_id = r.id
        WHERE e.student_id = ? AND e.status IN ('Pending', 'Dispatched', 'On-Scene')
        ORDER BY e.created_at DESC LIMIT 1
    """, (student_id,)).fetchone()

    # Past emergencies
    history = conn.execute("""
        SELECT e.*, r.full_name as responder_name
        FROM emergencies e
        LEFT JOIN users r ON e.responder_id = r.id
        WHERE e.student_id = ? AND e.status IN ('Resolved', 'Cancelled')
        ORDER BY e.created_at DESC
    """, (student_id,)).fetchall()

    # Notifications related to student's emergencies
    notifications = conn.execute("""
        SELECT n.*, e.emergency_type
        FROM notifications n
        JOIN emergencies e ON n.emergency_id = e.id
        WHERE e.student_id = ?
        ORDER BY n.sent_at DESC LIMIT 6
    """, (student_id,)).fetchall()

    user_info = conn.execute("SELECT * FROM users WHERE id = ?", (student_id,)).fetchone()
    conn.close()

    return render_template('student_dashboard.html',
                           active_emergency=active_emergency,
                           history=history,
                           notifications=notifications,
                           user_info=user_info)

# --- Responder Dashboard ---

@app.route('/responder/dashboard')
@login_required(roles=['responder', 'admin'])
def responder_dashboard():
    """Control Room & Quick Response Team Dashboard."""
    conn = get_db()
    
    # All active emergencies
    active_emergencies = conn.execute("""
        SELECT e.*, u.full_name as student_name, u.phone as student_phone, u.hostel_block, u.room_no,
               u.blood_group, u.medical_notes, u.emergency_contact_name, u.emergency_contact_phone,
               r.full_name as responder_name
        FROM emergencies e
        JOIN users u ON e.student_id = u.id
        LEFT JOIN users r ON e.responder_id = r.id
        WHERE e.status IN ('Pending', 'Dispatched', 'On-Scene')
        ORDER BY 
            CASE e.severity 
                WHEN 'Critical' THEN 1 
                WHEN 'High' THEN 2 
                ELSE 3 
            END,
            e.created_at DESC
    """, ).fetchall()

    # Recently resolved
    recent_resolved = conn.execute("""
        SELECT e.*, u.full_name as student_name, r.full_name as responder_name
        FROM emergencies e
        JOIN users u ON e.student_id = u.id
        LEFT JOIN users r ON e.responder_id = r.id
        WHERE e.status = 'Resolved'
        ORDER BY e.resolved_at DESC LIMIT 10
    """, ).fetchall()

    conn.close()
    return render_template('responder_dashboard.html',
                           active_emergencies=active_emergencies,
                           recent_resolved=recent_resolved)

# --- Admin Dashboard ---

@app.route('/admin/dashboard')
@login_required(roles=['admin'])
def admin_dashboard():
    """Chief Proctor / Administration Overview & Incident Analytics."""
    conn = get_db()
    
    # Summary Metrics
    total_emergencies = conn.execute("SELECT COUNT(*) FROM emergencies").fetchone()[0]
    active_emergencies = conn.execute("SELECT COUNT(*) FROM emergencies WHERE status IN ('Pending', 'Dispatched', 'On-Scene')").fetchone()[0]
    resolved_emergencies = conn.execute("SELECT COUNT(*) FROM emergencies WHERE status = 'Resolved'").fetchone()[0]
    total_students = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'student'").fetchone()[0]

    # Emergencies by Category
    category_counts = conn.execute("""
        SELECT emergency_type, COUNT(*) as count 
        FROM emergencies 
        GROUP BY emergency_type
    """).fetchall()

    # All Emergencies for Audit Log
    all_emergencies = conn.execute("""
        SELECT e.*, u.full_name as student_name, u.phone as student_phone, u.hostel_block, u.room_no,
               r.full_name as responder_name
        FROM emergencies e
        JOIN users u ON e.student_id = u.id
        LEFT JOIN users r ON e.responder_id = r.id
        ORDER BY e.created_at DESC
    """).fetchall()

    # Contacts Directory
    contacts = conn.execute("SELECT * FROM emergency_contacts ORDER BY id ASC").fetchall()

    conn.close()
    return render_template('admin_dashboard.html',
                           total_emergencies=total_emergencies,
                           active_emergencies=active_emergencies,
                           resolved_emergencies=resolved_emergencies,
                           total_students=total_students,
                           category_counts=category_counts,
                           all_emergencies=all_emergencies,
                           contacts=contacts)

# --- First Aid Guide & Directory Routes ---

@app.route('/first-aid')
def first_aid():
    """Searchable First Aid Guidelines."""
    category = request.args.get('category')
    search = request.args.get('search')
    
    conn = get_db()
    query = "SELECT * FROM first_aid_guides WHERE 1=1"
    params = []

    if category:
        query += " AND category = ?"
        params.append(category)

    if search:
        query += " AND (title LIKE ? OR symptoms LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    guides = conn.execute(query, params).fetchall()
    
    # Parse JSON for steps & dos_and_donts
    parsed_guides = []
    for g in guides:
        g_dict = dict(g)
        g_dict['steps'] = json.loads(g['steps_json']) if g['steps_json'] else []
        g_dict['dos_and_donts'] = json.loads(g['dos_and_donts_json']) if g['dos_and_donts_json'] else {"dos": [], "donts": []}
        parsed_guides.append(g_dict)

    categories = conn.execute("SELECT DISTINCT category FROM first_aid_guides").fetchall()
    conn.close()

    return render_template('first_aid.html', guides=parsed_guides, categories=[c['category'] for c in categories], selected_category=category, search_query=search)

@app.route('/campus-directory')
def campus_directory():
    """Campus Emergency Phone Directory."""
    conn = get_db()
    contacts = conn.execute("SELECT * FROM emergency_contacts WHERE is_active = 1 ORDER BY category, id").fetchall()
    conn.close()
    return render_template('campus_directory.html', contacts=contacts)

@app.route('/profile', methods=['GET', 'POST'])
@login_required()
def profile():
    """User profile management."""
    conn = get_db()
    user_id = session['user_id']

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        hostel_block = request.form.get('hostel_block', '').strip()
        room_no = request.form.get('room_no', '').strip()
        blood_group = request.form.get('blood_group', '').strip()
        medical_notes = request.form.get('medical_notes', '').strip()
        emergency_contact_name = request.form.get('emergency_contact_name', '').strip()
        emergency_contact_phone = request.form.get('emergency_contact_phone', '').strip()

        conn.execute("""
            UPDATE users SET
                full_name = ?, phone = ?, email = ?, hostel_block = ?, room_no = ?,
                blood_group = ?, medical_notes = ?, emergency_contact_name = ?, emergency_contact_phone = ?
            WHERE id = ?
        """, (full_name, phone, email, hostel_block, room_no, blood_group, medical_notes, emergency_contact_name, emergency_contact_phone, user_id))
        conn.commit()
        session['full_name'] = full_name
        flash('Profile updated successfully!', 'success')
        conn.close()
        return redirect(url_for('profile'))

    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return render_template('profile.html', user=user)

# --- REST APIs for Interactive Operations ---

@app.route('/api/emergency/create', methods=['POST'])
def api_create_emergency():
    """Trigger an Emergency SOS."""
    # Allow logged-in student or guest with credentials
    student_id = session.get('user_id')
    if not student_id:
        # Check if guest SOS submission
        return jsonify({'success': False, 'message': 'Please login to trigger an emergency SOS.'}), 401

    data = request.get_json() or request.form
    emergency_type = data.get('emergency_type', 'General Security')
    severity = data.get('severity', 'High')
    description = data.get('description', 'Instant SOS beacon triggered from student portal.')
    location_name = data.get('location_name', '').strip()
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    try:
        latitude = float(latitude) if latitude else 12.9716
        longitude = float(longitude) if longitude else 77.5946
    except (ValueError, TypeError):
        latitude, longitude = 12.9716, 77.5946

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (student_id,)).fetchone()

    if not location_name:
        location_name = f"{user['hostel_block'] or 'Campus Block'}, Room {user['room_no'] or 'N/A'}"

    # Insert Emergency
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO emergencies (student_id, emergency_type, severity, description, location_name, latitude, longitude, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')
    """, (student_id, emergency_type, severity, description, location_name, latitude, longitude))
    emergency_id = cursor.lastrowid

    # Create Automated Simulated Broadcasts (SMS / Email to Responders and Parent)
    # 1. Alert to Campus QRT
    cursor.execute("""
        INSERT INTO notifications (emergency_id, recipient_role, recipient_name, recipient_contact, message, channel)
        VALUES (?, 'Responder', 'Campus Emergency Central', '+91 98765 00100', ?, 'SMS Simulation')
    """, (emergency_id, f"SOS ALERT: {emergency_type.upper()} reported by {user['full_name']} at {location_name}. Blood Group: {user['blood_group'] or 'N/A'}."))

    # 2. Alert to Student's Emergency Contact / Parents
    if user['emergency_contact_phone']:
        cursor.execute("""
            INSERT INTO notifications (emergency_id, recipient_role, recipient_name, recipient_contact, message, channel)
            VALUES (?, 'Parent/Guardian', ?, ?, ?, 'SMS Simulation')
        """, (emergency_id, user['emergency_contact_name'] or 'Emergency Contact', user['emergency_contact_phone'],
              f"CAMPUS SAFETY ALERT: An emergency assistance alert was triggered for {user['full_name']} at {location_name}. Campus response team has been alerted."))

    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'emergency_id': emergency_id,
        'message': '🚨 Emergency SOS broadcasted! Responders and emergency contacts have been notified.'
    })

@app.route('/api/emergency/cancel/<int:emergency_id>', methods=['POST'])
@login_required()
def api_cancel_emergency(emergency_id):
    """Allows student to cancel pending emergency if triggered mistakenly."""
    conn = get_db()
    emergency = conn.execute("SELECT * FROM emergencies WHERE id = ?", (emergency_id,)).fetchone()
    
    if not emergency:
        conn.close()
        return jsonify({'success': False, 'message': 'Incident not found.'}), 404

    # Allow creator or admin
    if session.get('role') != 'admin' and emergency['student_id'] != session.get('user_id'):
        conn.close()
        return jsonify({'success': False, 'message': 'Unauthorized action.'}), 403

    conn.execute("UPDATE emergencies SET status = 'Cancelled', responder_notes = 'Cancelled by student (false alarm)' WHERE id = ?", (emergency_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Emergency request cancelled.'})

@app.route('/api/emergency/update-status/<int:emergency_id>', methods=['POST'])
@login_required(roles=['responder', 'admin'])
def api_update_emergency_status(emergency_id):
    """Responder or Admin updates incident progress."""
    data = request.get_json() or request.form
    new_status = data.get('status')
    eta_minutes = data.get('eta_minutes')
    notes = data.get('responder_notes', '')

    if new_status not in ['Pending', 'Dispatched', 'On-Scene', 'Resolved', 'Cancelled']:
        return jsonify({'success': False, 'message': 'Invalid status provided.'}), 400

    conn = get_db()
    responder_id = session.get('user_id')

    resolved_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if new_status == 'Resolved' else None

    conn.execute("""
        UPDATE emergencies SET
            status = ?,
            responder_id = COALESCE(?, responder_id),
            eta_minutes = COALESCE(?, eta_minutes),
            responder_notes = COALESCE(?, responder_notes),
            resolved_at = COALESCE(?, resolved_at)
        WHERE id = ?
    """, (new_status, responder_id, eta_minutes, notes, resolved_at, emergency_id))
    
    # Notify student of status change
    emergency = conn.execute("SELECT e.*, u.full_name as student_name, u.phone as student_phone FROM emergencies e JOIN users u ON e.student_id = u.id WHERE e.id = ?", (emergency_id,)).fetchone()
    if emergency:
        status_msg = f"Update on Incident #{emergency_id}: Status changed to {new_status}."
        if eta_minutes:
            status_msg += f" Estimated arrival time: {eta_minutes} mins."
        conn.execute("""
            INSERT INTO notifications (emergency_id, recipient_role, recipient_name, recipient_contact, message, channel)
            VALUES (?, 'Student', ?, ?, ?, 'System Push')
        """, (emergency_id, emergency['student_name'], emergency['student_phone'], status_msg))

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': f'Incident #{emergency_id} status updated to {new_status}.'})

@app.route('/api/emergencies/active', methods=['GET'])
def api_get_active_emergencies():
    """Returns active emergencies for real-time polling and map rendering."""
    conn = get_db()
    emergencies = conn.execute("""
        SELECT e.id, e.emergency_type, e.severity, e.description, e.location_name,
               e.latitude, e.longitude, e.status, e.eta_minutes, e.created_at,
               u.full_name as student_name, u.phone as student_phone, u.blood_group,
               u.hostel_block, u.room_no,
               r.full_name as responder_name
        FROM emergencies e
        JOIN users u ON e.student_id = u.id
        LEFT JOIN users r ON e.responder_id = r.id
        WHERE e.status IN ('Pending', 'Dispatched', 'On-Scene')
        ORDER BY e.created_at DESC
    """).fetchall()
    conn.close()

    result = [dict(row) for row in emergencies]
    return jsonify({'success': True, 'count': len(result), 'emergencies': result})

@app.route('/api/emergency/<int:emergency_id>', methods=['GET'])
@login_required()
def api_get_emergency_details(emergency_id):
    """Retrieve full details of an incident including student profile."""
    conn = get_db()
    row = conn.execute("""
        SELECT e.*, u.full_name as student_name, u.phone as student_phone, u.email as student_email,
               u.hostel_block, u.room_no, u.blood_group, u.medical_notes,
               u.emergency_contact_name, u.emergency_contact_phone,
               r.full_name as responder_name, r.phone as responder_phone
        FROM emergencies e
        JOIN users u ON e.student_id = u.id
        LEFT JOIN users r ON e.responder_id = r.id
        WHERE e.id = ?
    """, (emergency_id,)).fetchone()
    conn.close()

    if not row:
        return jsonify({'success': False, 'message': 'Incident not found'}), 404

    return jsonify({'success': True, 'data': dict(row)})

# --- Admin Directory Management ---

@app.route('/api/directory/add', methods=['POST'])
@login_required(roles=['admin'])
def api_add_directory_contact():
    """Add new campus emergency contact."""
    category = request.form.get('category', '').strip()
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    description = request.form.get('description', '').strip()
    availability = request.form.get('availability', '24/7').strip()

    if not name or not phone:
        flash('Name and phone number are required.', 'danger')
        return redirect(url_for('admin_dashboard'))

    conn = get_db()
    conn.execute("""
        INSERT INTO emergency_contacts (category, name, phone, description, availability)
        VALUES (?, ?, ?, ?, ?)
    """, (category, name, phone, description, availability))
    conn.commit()
    conn.close()
    flash('New emergency contact added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/api/directory/delete/<int:contact_id>', methods=['POST'])
@login_required(roles=['admin'])
def api_delete_directory_contact(contact_id):
    """Delete a campus emergency contact."""
    conn = get_db()
    conn.execute("DELETE FROM emergency_contacts WHERE id = ?", (contact_id,))
    conn.commit()
    conn.close()
    flash('Emergency contact removed.', 'info')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    # Run development server (host='0.0.0.0' allows other devices on same Wi-Fi)
    import socket
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    local_ip = get_local_ip()

    print("=" * 65)
    print(" [*] CAMPUS EMERGENCY ASSISTANCE PORTAL SERVER RUNNING")
    print(f" -> Local (this PC):       http://127.0.0.1:5000")
    print(f" -> Other Devices (Wi-Fi): http://{local_ip}:5000")
    print("=" * 65)
    print(" Default Accounts:")
    print("  Student:   student1   / password123")
    print("  Responder: security1  / security123")
    print("  Admin:     admin      / admin123")
    print("=" * 65)
    app.run(host='0.0.0.0', port=5000, debug=False)


