import os
import unittest
import json
from app import app
from database import init_db, get_db

class TestCollegeEmergencyPortal(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        init_db()

    def test_01_landing_page(self):
        """Test public home page loads with 200 OK and emergency banners."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Student Emergency Assistance Portal', response.data)
        self.assertIn(b'Ambulance', response.data)

    def test_02_student_login(self):
        """Test authentication for student demo account."""
        response = self.client.post('/login', data={
            'username': 'student1',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Alex Rivera', response.data)
        self.assertIn(b'Student Safety Console', response.data)

    def test_03_trigger_sos_api(self):
        """Test triggering emergency SOS via API as a logged-in student."""
        # Login first
        self.client.post('/login', data={'username': 'student1', 'password': 'password123'})
        
        # Post SOS
        response = self.client.post('/api/emergency/create',
            data=json.dumps({
                'emergency_type': 'Medical Emergency',
                'severity': 'Critical',
                'location_name': 'Library 2nd Floor, Study Hall',
                'description': 'Student fainted and unresponsive',
                'latitude': 12.9716,
                'longitude': 77.5946
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('emergency_id', data)
        self.emergency_id = data['emergency_id']

        # Verify incident is in DB
        conn = get_db()
        row = conn.execute("SELECT * FROM emergencies WHERE id = ?", (self.emergency_id,)).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row['status'], 'Pending')
        self.assertEqual(row['location_name'], 'Library 2nd Floor, Study Hall')

        # Verify automated simulated notifications were logged
        notifications = conn.execute("SELECT * FROM notifications WHERE emergency_id = ?", (self.emergency_id,)).fetchall()
        self.assertGreaterEqual(len(notifications), 1)
        conn.close()

    def test_04_responder_dispatch_api(self):
        """Test responder taking incident, updating ETA, and marking resolved."""
        # Login as responder
        self.client.post('/login', data={'username': 'security1', 'password': 'security123'})

        conn = get_db()
        incident = conn.execute("SELECT id FROM emergencies WHERE status = 'Pending' LIMIT 1").fetchone()
        conn.close()

        if incident:
            inc_id = incident['id']
            # Update to Dispatched
            res1 = self.client.post(f'/api/emergency/update-status/{inc_id}',
                data=json.dumps({'status': 'Dispatched', 'eta_minutes': 3, 'responder_notes': 'QRT unit mobilised'}),
                content_type='application/json'
            )
            self.assertEqual(res1.status_code, 200)

            # Update to Resolved
            res2 = self.client.post(f'/api/emergency/update-status/{inc_id}',
                data=json.dumps({'status': 'Resolved', 'responder_notes': 'Student examined, stable.'}),
                content_type='application/json'
            )
            self.assertEqual(res2.status_code, 200)

            conn = get_db()
            updated = conn.execute("SELECT status, responder_notes FROM emergencies WHERE id = ?", (inc_id,)).fetchone()
            self.assertEqual(updated['status'], 'Resolved')
            conn.close()

    def test_05_first_aid_page(self):
        """Test First Aid protocols page with search and category filtering."""
        response = self.client.get('/first-aid')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Cardiopulmonary Resuscitation (CPR)', response.data)
        self.assertIn(b'Severe Bleeding', response.data)

        # Search test
        search_res = self.client.get('/first-aid?search=CPR')
        self.assertEqual(search_res.status_code, 200)
        self.assertIn(b'CPR', search_res.data)

    def test_06_campus_directory(self):
        """Test Campus Directory page."""
        response = self.client.get('/campus-directory')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'+91 98765 00108', response.data)
        self.assertIn(b'Ambulance', response.data)

    def test_07_active_emergencies_api(self):
        """Test live radar polling endpoint."""
        response = self.client.get('/api/emergencies/active')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIsInstance(data['emergencies'], list)

if __name__ == '__main__':
    unittest.main()
