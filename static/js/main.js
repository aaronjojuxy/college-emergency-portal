/**
 * COLLEGE EMERGENCY ASSISTANCE PORTAL - JAVASCRIPT ENGINE
 * Handles: Geolocation, Web Audio API Siren, Real-time AJAX polling, SOS triggers, Leaflet Campus Maps.
 */

// --- Audio Siren Synthesizer (Native Web Audio API) ---
let audioCtx = null;
let sirenOscillator = null;
let sirenGain = null;
let isSirenPlaying = false;
let sirenInterval = null;

function initAudio() {
    if (!audioCtx) {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        audioCtx = new AudioContext();
    }
}

function playSiren() {
    try {
        initAudio();
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
        if (isSirenPlaying) return;

        sirenOscillator = audioCtx.createOscillator();
        sirenGain = audioCtx.createGain();

        sirenOscillator.type = 'sawtooth';
        sirenOscillator.frequency.setValueAtTime(650, audioCtx.currentTime);

        // Modulate frequency to create oscillating emergency siren
        let high = false;
        sirenInterval = setInterval(() => {
            if (!audioCtx || !sirenOscillator) return;
            const now = audioCtx.currentTime;
            sirenOscillator.frequency.cancelScheduledValues(now);
            sirenOscillator.frequency.linearRampToValueAtTime(high ? 650 : 980, now + 0.35);
            high = !high;
        }, 400);

        sirenGain.gain.setValueAtTime(0.15, audioCtx.currentTime);
        sirenOscillator.connect(sirenGain);
        sirenGain.connect(audioCtx.destination);
        sirenOscillator.start();
        isSirenPlaying = true;
        updateSirenBadgeUI(true);
    } catch (e) {
        console.warn("Web Audio API not allowed yet by browser autoplay policy:", e);
    }
}

function stopSiren() {
    if (sirenInterval) {
        clearInterval(sirenInterval);
        sirenInterval = null;
    }
    if (sirenOscillator) {
        try {
            sirenOscillator.stop();
            sirenOscillator.disconnect();
        } catch (e) {}
        sirenOscillator = null;
    }
    isSirenPlaying = false;
    updateSirenBadgeUI(false);
}

function toggleSiren() {
    if (isSirenPlaying) {
        stopSiren();
    } else {
        playSiren();
    }
}

function updateSirenBadgeUI(playing) {
    const badges = document.querySelectorAll('.siren-badge');
    badges.forEach(badge => {
        if (playing) {
            badge.classList.remove('muted');
            badge.classList.add('active');
            badge.innerHTML = '<i class="fa-solid fa-volume-high fa-beat"></i> Siren Active (Click to Mute)';
        } else {
            badge.classList.remove('active');
            badge.classList.add('muted');
            badge.innerHTML = '<i class="fa-solid fa-volume-xmark"></i> Siren Muted';
        }
    });
}

// --- HTML5 Geolocation ---
let userCoords = { latitude: 12.9716, longitude: 77.5946, accuracy: null };

function detectLocation(callback) {
    if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                userCoords.latitude = pos.coords.latitude;
                userCoords.longitude = pos.coords.longitude;
                userCoords.accuracy = pos.coords.accuracy;
                console.log("GPS Location acquired:", userCoords);
                if (callback) callback(userCoords);
            },
            (err) => {
                console.warn("Geolocation denied or unavailable. Using default campus block coords.", err.message);
                if (callback) callback(userCoords);
            },
            { enableHighAccuracy: true, timeout: 6000 }
        );
    } else {
        if (callback) callback(userCoords);
    }
}

// --- SOS Panic Trigger Handlers ---
let sosCountdownTimer = null;
let countdownRemaining = 4;

function startSosCountdown(type, severity) {
    detectLocation();
    const modalEl = document.getElementById('sosConfirmModal');
    if (!modalEl) {
        triggerSosDirect(type, severity);
        return;
    }

    const modal = new bootstrap.Modal(modalEl);
    const counterEl = document.getElementById('sosCountdownVal');
    const sendBtn = document.getElementById('sosSendNowBtn');
    const cancelBtn = document.getElementById('sosCancelBtn');
    const typeLabel = document.getElementById('sosModalTypeLabel');

    if (typeLabel) typeLabel.innerText = type;

    countdownRemaining = 4;
    if (counterEl) counterEl.innerText = countdownRemaining;
    modal.show();

    if (sosCountdownTimer) clearInterval(sosCountdownTimer);
    sosCountdownTimer = setInterval(() => {
        countdownRemaining--;
        if (counterEl) counterEl.innerText = countdownRemaining;
        if (countdownRemaining <= 0) {
            clearInterval(sosCountdownTimer);
            modal.hide();
            triggerSosDirect(type, severity);
        }
    }, 1000);

    sendBtn.onclick = function() {
        clearInterval(sosCountdownTimer);
        modal.hide();
        triggerSosDirect(type, severity);
    };

    cancelBtn.onclick = function() {
        clearInterval(sosCountdownTimer);
        modal.hide();
    };
}

function triggerSosDirect(emergencyType, severity) {
    const locationInput = document.getElementById('sosLocationInput');
    const descInput = document.getElementById('sosDescInput');

    const payload = {
        emergency_type: emergencyType || 'General Security',
        severity: severity || 'High',
        location_name: locationInput ? locationInput.value : '',
        description: descInput ? descInput.value : 'Instant SOS Panic Triggered',
        latitude: userCoords.latitude,
        longitude: userCoords.longitude
    };

    fetch('/api/emergency/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            playSiren();
            alert("🚨 SOS BROADCASTED!\n\nCampus Security and Medical Responders have received your emergency alert with your current location. Please remain calm.");
            window.location.reload();
        } else {
            alert(data.message || "Failed to broadcast emergency SOS. Please dial Campus Emergency hotline directly.");
        }
    })
    .catch(err => {
        console.error("SOS Trigger Error:", err);
        alert("Network error triggering SOS. Please immediately call the campus security hotline: +91 98765 00100");
    });
}

// --- Cancel Emergency ---
function cancelEmergency(emergencyId) {
    if (!confirm("Are you sure you want to cancel this emergency request?")) return;

    fetch(`/api/emergency/cancel/${emergencyId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            stopSiren();
            alert("Emergency request has been cancelled.");
            window.location.reload();
        } else {
            alert(data.message || "Error cancelling request.");
        }
    });
}

// --- Responder Status Update ---
function updateIncidentStatus(emergencyId, newStatus) {
    let eta = null;
    let notes = prompt(`Enter optional remarks/notes for status '${newStatus}':`);
    if (notes === null) return; // user cancelled prompt

    if (newStatus === 'Dispatched') {
        const etaInput = prompt("Estimated Arrival Time (ETA in minutes):", "5");
        if (etaInput !== null) eta = parseInt(etaInput) || 5;
    }

    fetch(`/api/emergency/update-status/${emergencyId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            status: newStatus,
            eta_minutes: eta,
            responder_notes: notes
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        } else {
            alert(data.message || "Failed to update incident.");
        }
    });
}

// --- Interactive Campus Map using Leaflet.js ---
let campusMapInstance = null;
let campusMapMarkers = [];

function initCampusMap(mapElementId, defaultLat, defaultLon) {
    const el = document.getElementById(mapElementId);
    if (!el) return;

    const centerLat = defaultLat || 12.9716;
    const centerLon = defaultLon || 77.5946;

    campusMapInstance = L.map(mapElementId).setView([centerLat, centerLon], 16);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors | College Emergency System',
        maxZoom: 19
    }).addTo(campusMapInstance);

    // Refresh beacons on map
    loadMapEmergencyBeacons();
}

function loadMapEmergencyBeacons() {
    if (!campusMapInstance) return;

    fetch('/api/emergencies/active')
    .then(res => res.json())
    .then(data => {
        if (!data.success) return;

        // Clear existing markers
        campusMapMarkers.forEach(m => campusMapInstance.removeLayer(m));
        campusMapMarkers = [];

        data.emergencies.forEach(item => {
            const lat = item.latitude || 12.9716;
            const lon = item.longitude || 77.5946;

            const iconHtml = `<div style="background-color: ${item.severity === 'Critical' ? '#dc3545' : '#f97316'}; color: white; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; border: 3px solid white; box-shadow: 0 0 12px rgba(220,53,69,0.8);"><i class="fa-solid fa-triangle-exclamation"></i></div>`;
            const customIcon = L.divIcon({
                className: 'campus-emergency-pin',
                html: iconHtml,
                iconSize: [34, 34],
                iconAnchor: [17, 17]
            });

            const marker = L.marker([lat, lon], { icon: customIcon }).addTo(campusMapInstance);

            const popupContent = `
                <div style="min-width: 200px;">
                    <div style="font-weight: bold; color: #dc3545; font-size: 1.05rem;">
                        <i class="fa-solid fa-bell"></i> ${item.emergency_type} (${item.severity})
                    </div>
                    <div style="margin: 4px 0; font-size: 0.9rem;">
                        <strong>Student:</strong> ${item.student_name} (${item.blood_group || 'Blood N/A'})
                    </div>
                    <div style="font-size: 0.85rem; color: #475569;">
                        <i class="fa-solid fa-location-dot"></i> ${item.location_name}
                    </div>
                    <div style="margin-top: 6px; font-size: 0.85rem;">
                        <strong>Status:</strong> <span class="badge bg-danger">${item.status}</span>
                    </div>
                    <div style="margin-top: 8px;">
                        <a href="tel:${item.student_phone}" class="btn btn-sm btn-outline-danger w-100">
                            <i class="fa-solid fa-phone"></i> Call Student (${item.student_phone})
                        </a>
                    </div>
                </div>
            `;
            marker.bindPopup(popupContent);
            campusMapMarkers.push(marker);
        });
    });
}

// --- Real-time Polling for Live Incidents (Responder & Admin) ---
let lastKnownActiveCount = -1;

function startLivePolling() {
    setInterval(() => {
        fetch('/api/emergencies/active')
        .then(res => res.json())
        .then(data => {
            if (!data.success) return;

            const badge = document.getElementById('navActiveBadge');
            if (badge) {
                badge.innerText = data.count;
                if (data.count > 0) {
                    badge.classList.remove('d-none');
                } else {
                    badge.classList.add('d-none');
                }
            }

            // If new emergency appeared, trigger alert sound
            if (lastKnownActiveCount !== -1 && data.count > lastKnownActiveCount) {
                playSiren();
            }
            lastKnownActiveCount = data.count;

            // If map is present, update markers
            if (campusMapInstance) {
                loadMapEmergencyBeacons();
            }
        })
        .catch(err => console.debug("Polling error:", err));
    }, 6000);
}

// Document Ready Initialization
document.addEventListener('DOMContentLoaded', () => {
    // Detect geolocation in background for fast SOS submission
    detectLocation();

    // Start background polling
    startLivePolling();

    // Category card click selector on student dashboard
    const catCards = document.querySelectorAll('.category-card');
    catCards.forEach(card => {
        card.addEventListener('click', () => {
            catCards.forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            const typeVal = card.getAttribute('data-type');
            const hiddenType = document.getElementById('selectedEmergencyType');
            if (hiddenType) hiddenType.value = typeVal;
        });
    });
});
