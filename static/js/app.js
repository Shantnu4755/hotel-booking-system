// API Configuration
const API_BASE = window.location.origin;
let currentUser = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    checkAuthStatus();
    loadBookings();

    // Set dynamic year in footer
    const yearSpan = document.getElementById('currentYear');
    if (yearSpan) {
        yearSpan.textContent = new Date().getFullYear();
    }
});

// Initialize application
function initializeApp() {
    // Set default datetime values (tomorrow)
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(10, 0, 0, 0);
    
    const dayAfter = new Date(tomorrow);
    dayAfter.setDate(dayAfter.getDate() + 1);
    dayAfter.setHours(14, 0, 0, 0);
    
    document.getElementById('checkIn').value = formatDateTimeLocal(tomorrow);
    document.getElementById('checkOut').value = formatDateTimeLocal(dayAfter);
    
    // Search form handler
    document.getElementById('searchForm').addEventListener('submit', handleSearch);
    
    // Booking form handlers
    document.getElementById('confirmBookingBtn').addEventListener('click', handleConfirmBooking);
    document.getElementById('refreshBookingsBtn').addEventListener('click', loadBookings);
    
    // Auto-update price when booking form changes
    ['bookingCheckIn', 'bookingCheckOut', 'bookingTypeSelect'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('change', calculateEstimatedPrice);
        }
    });
    
    // Auth form handlers
    document.getElementById('loginSubmitBtn').addEventListener('click', handleLogin);
    document.getElementById('signupSubmitBtn').addEventListener('click', handleSignup);
}

// Format datetime for input[type="datetime-local"]
function formatDateTimeLocal(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
}

// Convert datetime-local to ISO string
function datetimeLocalToISO(datetimeLocal) {
    if (!datetimeLocal) return null;
    const date = new Date(datetimeLocal);
    return date.toISOString();
}

// Sample room images for a richer, more visual UI
const ROOM_IMAGES = [
    "https://placehold.co/600x400/1a1f3b/ffffff?text=Royal+Room",
    "https://placehold.co/600x400/c9a34b/111827?text=Executive+Suite",
    "https://placehold.co/600x400/0f766e/ffffff?text=Luxury+Suite",
    "https://placehold.co/600x400/b91c1c/ffffff?text=Heritage+Room",
    "https://placehold.co/600x400/111827/e5e7eb?text=Premium+Twin",
    "https://placehold.co/600x400/f5f1e8/111827?text=Garden+View",
    "https://placehold.co/600x400/1e40af/ffffff?text=Family+Suite",
    "https://placehold.co/600x400/0b1020/e5e7eb?text=City+View",
    "https://placehold.co/600x400/065f46/ffffff?text=Wellness",
    "https://placehold.co/600x400/fef3c7/92400e?text=Presidential",
];

// Match backend pricing rules: ceil(hours/days) * base_price
function calculatePriceForRoom(room, start, end, bookingType) {
    const durationSeconds = (end - start) / 1000;
    if (!durationSeconds || durationSeconds <= 0) return 0;

    if (bookingType === 'HOURLY') {
        const hours = Math.ceil(durationSeconds / 3600);
        return hours * parseFloat(room.base_price_per_hour);
    }

    const days = Math.ceil(durationSeconds / 86400);
    return days * parseFloat(room.base_price_per_day);
}

// Get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// API Fetch with error handling
async function apiFetch(path, options = {}) {
    try {
        const headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            ...options.headers
        };
        
        const fetchOptions = {
            ...options,
            headers,
            credentials: 'include' // Include cookies for session auth
        };
        
        const response = await fetch(`${API_BASE}${path}`, fetchOptions);
        
        const data = await response.json().catch(() => ({}));
        
        if (!response.ok) {
            // Handle authentication errors gracefully
            if (response.status === 401 || response.status === 403) {
                const errorMsg = data.detail || data.message || 'Authentication required';
                showToast(errorMsg + '. For booking Room, please log in', 'warning');
                return { status: response.status, data };
            }
            throw new Error(data.detail || data.message || 'Invalid credentials! Please try again with correct credentials');
        }
        
        return { status: response.status, data };
    } catch (error) {
        showToast(error.message, 'danger');
        throw error;
    }
}

// Handle room search
async function handleSearch(e) {
    e.preventDefault();
    
    const checkIn = document.getElementById('checkIn').value;
    const checkOut = document.getElementById('checkOut').value;
    const bookingType = document.getElementById('bookingType').value;
    
    if (!checkIn || !checkOut) {
        showToast('Please select both check-in and check-out dates', 'warning');
        return;
    }
    
    const startISO = datetimeLocalToISO(checkIn);
    const endISO = datetimeLocalToISO(checkOut);
    
    if (new Date(endISO) <= new Date(startISO)) {
        showToast('Check-out must be after check-in', 'warning');
        return;
    }
    
    try {
        showLoading('roomsContainer');
        const response = await apiFetch(
            `/api/rooms/available/?start_datetime=${encodeURIComponent(startISO)}&end_datetime=${encodeURIComponent(endISO)}&booking_type=${bookingType}`
        );
        
        displayRooms(response.data, bookingType);
    } catch (error) {
        displayRooms([]);
    }
}

// Display available rooms
function displayRooms(rooms, bookingType = 'DAILY') {
    const container = document.getElementById('roomsContainer');

    if (!rooms || rooms.length === 0) {
        container.innerHTML = `
            <div class="col-12 text-center text-muted py-5">
                <i class="fas fa-bed fa-3x mb-3"></i>
                <p class="h5">No rooms available for the selected dates</p>
                <p>Try different dates or booking type</p>
            </div>
        `;
        return;
    }

    const checkInVal = document.getElementById('checkIn').value;
    const checkOutVal = document.getElementById('checkOut').value;
    const start = checkInVal ? new Date(datetimeLocalToISO(checkInVal)) : null;
    const end = checkOutVal ? new Date(datetimeLocalToISO(checkOutVal)) : null;

    container.innerHTML = rooms.map((room, index) => {
        console.log("ROOM:", room.name, "LOGO:", room.logo?.slice(0, 50));
        const imageUrl =
                room.logo;
        if (start && end) {
            const totalPrice = calculatePriceForRoom(room, start, end, bookingType);
            if (totalPrice > 0 && isFinite(totalPrice)) {
                const durationSeconds = (end - start) / 1000;
                let durationLabel = '';

                if (bookingType === 'HOURLY') {
                    const hours = Math.ceil(durationSeconds / 3600);
                    durationLabel = `${hours} ${hours === 1 ? 'hour' : 'hours'}`;
                } else {
                    const days = Math.ceil(durationSeconds / 86400);
                    durationLabel = `${days} ${days === 1 ? 'night' : 'nights'}`;
                }

                totalPriceHtml = `
                    <div class="room-total mt-2">
                        <small class="text-muted">Est. total for ${durationLabel}</small>
                        <div class="room-total-amount">$${totalPrice.toFixed(2)}</div>
                    </div>`;
            }
        }

        const basePrice = bookingType === 'HOURLY'
            ? `$${parseFloat(room.base_price_per_hour).toFixed(2)}`
            : `$${parseFloat(room.base_price_per_day).toFixed(2)}`;
        const baseUnit = bookingType === 'HOURLY' ? 'hour' : 'day';

        return `
        <div class="col-md-6 col-lg-4 fade-in">
            <div class="card room-card h-100">
                <div class="room-image-wrapper">
                    <img src="${imageUrl}" alt="${escapeHtml(room.name)}" class="room-image">
                    <span class="room-tag badge bg-warning text-dark">Premium</span>
                </div>
                <div class="room-card-header">
                    <h4 class="mb-0">${escapeHtml(room.name)}</h4>
                    <small>Capacity: ${room.capacity} ${room.capacity === 1 ? 'person' : 'people'}</small>
                </div>
                <div class="room-card-body">
                    <p class="text-muted mb-3">${escapeHtml(room.description || 'Thoughtfully designed room with refined interiors and modern amenities.')}</p>
                    <ul class="room-features">
                        <li><i class="fas fa-check-circle"></i> Air Conditioning</li>
                        <li><i class="fas fa-check-circle"></i> Complimentary Wi-Fi</li>
                        <li><i class="fas fa-check-circle"></i> 24x7 Room Service</li>
                    </ul>
                    <div class="mt-4">
                        <div class="room-price">
                            ${basePrice}
                            <span class="room-price-unit">/ ${baseUnit}</span>
                        </div>
                        ${totalPriceHtml}
                    </div>
                    <button class="btn btn-primary w-100 mt-3" onclick="openBookingModal(${room.id}, '${escapeHtml(room.name)}', '${bookingType}')">
                        <i class="fas fa-calendar-check me-2"></i>Book Now
                    </button>
                </div>
            </div>
        </div>
        `;
    }).join('');
}

// Open booking modal
function openBookingModal(roomId, roomName, bookingType) {
    const checkIn = document.getElementById('checkIn').value;
    const checkOut = document.getElementById('checkOut').value;
    
    document.getElementById('selectedRoomId').value = roomId;
    document.getElementById('selectedRoomName').value = roomName;
    document.getElementById('bookingCheckIn').value = checkIn;
    document.getElementById('bookingCheckOut').value = checkOut;
    document.getElementById('bookingTypeSelect').value = bookingType;
    
    calculateEstimatedPrice();
    
    const modal = new bootstrap.Modal(document.getElementById('bookingModal'));
    modal.show();
}

// Calculate estimated price
async function calculateEstimatedPrice() {
    const roomId = document.getElementById('selectedRoomId').value;
    const checkIn = document.getElementById('bookingCheckIn').value;
    const checkOut = document.getElementById('bookingCheckOut').value;
    const bookingType = document.getElementById('bookingTypeSelect').value;
    
    if (!roomId || !checkIn || !checkOut) {
        document.getElementById('estimatedPrice').textContent = 'Please fill all fields';
        return;
    }
    
    try {
        // Get room details
        const roomResponse = await apiFetch(`/api/rooms/${roomId}/`);
        const room = roomResponse.data;
        
        const start = new Date(datetimeLocalToISO(checkIn));
        const end = new Date(datetimeLocalToISO(checkOut));
        const price = calculatePriceForRoom(room, start, end, bookingType);

        if (!price || !isFinite(price) || price <= 0) {
            document.getElementById('estimatedPrice').textContent = 'Unable to calculate';
            return;
        }

        document.getElementById('estimatedPrice').textContent = `$${price.toFixed(2)}`;
    } catch (error) {
        document.getElementById('estimatedPrice').textContent = 'Unable to calculate';
    }
}

// Handle booking confirmation
async function handleConfirmBooking() {
    const roomId = document.getElementById('selectedRoomId').value;
    const checkIn = document.getElementById('bookingCheckIn').value;
    const checkOut = document.getElementById('bookingCheckOut').value;
    const bookingType = document.getElementById('bookingTypeSelect').value;
    
    if (!roomId || !checkIn || !checkOut) {
        showToast('Please fill all fields', 'warning');
        return;
    }
    
    const startISO = datetimeLocalToISO(checkIn);
    const endISO = datetimeLocalToISO(checkOut);
    
    try {
        const response = await apiFetch('/api/bookings/', {
            method: 'POST',
            body: JSON.stringify({
                room_id: parseInt(roomId),
                booking_type: bookingType,
                start_datetime: startISO,
                end_datetime: endISO
            })
        });
        
        if (response.status === 201) {
            showToast('Booking confirmed successfully!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('bookingModal')).hide();
            loadBookings();
        } else if (response.status === 401 || response.status === 403) {
            showToast('Please log in to create bookings', 'warning');
        }
    } catch (error) {
        // Error already shown by apiFetch
    }
}

// Load user bookings
async function loadBookings() {
    try {
        showLoading('bookingsContainer');
        const response = await apiFetch('/api/bookings/');
        if (response.status === 200) {
            displayBookings(response.data.results || response.data);
        } else {
            displayBookings([]);
        }
    } catch (error) {
        // If auth error, show helpful message
        if (error.message && error.message.includes('Authentication')) {
            const container = document.getElementById('bookingsContainer');
            container.innerHTML = `
                <div class="col-12 text-center text-muted py-5">
                    <i class="fas fa-lock fa-3x mb-3"></i>
                    <p class="h5">Authentication Required</p>
                    <p>Please <a href="/admin/" target="_blank">log in</a> to view your bookings</p>
                </div>
            `;
        } else {
            displayBookings([]);
        }
    }
}

// Display bookings
function displayBookings(bookings) {
    const container = document.getElementById('bookingsContainer');
    
    if (!bookings || bookings.length === 0) {
        container.innerHTML = `
            <div class="col-12 text-center text-muted py-5">
                <i class="fas fa-calendar fa-3x mb-3"></i>
                <p class="h5">No bookings yet</p>
                <p>Book a room to get started!</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = bookings.map(booking => {
        const startDate = new Date(booking.start_datetime);
        const endDate = new Date(booking.end_datetime);
        const statusClass = booking.status.toLowerCase().replace('_', '-');
        
        return `
            <div class="col-12 fade-in">
                <div class="card booking-card ${statusClass}">
                    <div class="card-body">
                        <div class="row align-items-center">
                            <div class="col-md-6">
                                <h5 class="mb-2">${escapeHtml(booking.room.name)}</h5>
                                <p class="text-muted mb-2">
                                    <i class="fas fa-calendar-alt me-2"></i>
                                    ${formatDate(startDate)} - ${formatDate(endDate)}
                                </p>
                                <p class="text-muted mb-0">
                                    <i class="fas fa-clock me-2"></i>
                                    ${formatTime(startDate)} - ${formatTime(endDate)}
                                </p>
                            </div>
                            <div class="col-md-3 text-center">
                                <span class="status-badge ${statusClass}">${booking.status.replace('_', ' ')}</span>
                                <div class="mt-2">
                                    <strong class="text-primary">$${parseFloat(booking.total_price).toFixed(2)}</strong>
                                </div>
                            </div>
                            <div class="col-md-3 text-end">
                                ${getBookingActions(booking)}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Get booking action buttons
function getBookingActions(booking) {
    const status = booking.status;
    const now = new Date();
    const startDate = new Date(booking.start_datetime);
    
    let actions = '';
    
    if (status === 'CONFIRMED' && now >= startDate) {
        actions += `<button class="btn btn-warning btn-sm btn-action" onclick="bookingAction(${booking.id}, 'check-in')">
            <i class="fas fa-sign-in-alt me-1"></i>Check-in
        </button>`;
    }
    
    if (status === 'CHECKED_IN') {
        actions += `<button class="btn btn-success btn-sm btn-action" onclick="bookingAction(${booking.id}, 'check-out')">
            <i class="fas fa-sign-out-alt me-1"></i>Check-out
        </button>`;
    }
    
    if (status === 'CONFIRMED' && now < startDate) {
        actions += `<button class="btn btn-danger btn-sm btn-action" onclick="bookingAction(${booking.id}, 'cancel')">
            <i class="fas fa-times me-1"></i>Cancel
        </button>`;
    }
    
    return actions || '<span class="text-muted">No actions available</span>';
}

// Handle booking actions
async function bookingAction(bookingId, action) {
    if (!confirm(`Are you sure you want to ${action.replace('-', ' ')} this booking?`)) {
        return;
    }
    
    try {
        await apiFetch(`/api/bookings/${bookingId}/${action}/`, {
            method: 'POST'
        });
        
        showToast(`Booking ${action.replace('-', ' ')} successful!`, 'success');
        loadBookings();
    } catch (error) {
        // Error already shown
    }
}

// Utility functions
function formatDate(date) {
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

function formatTime(date) {
    return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showLoading(containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = `
        <div class="col-12 text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastBody = toast.querySelector('.toast-body');
    const toastHeader = toast.querySelector('.toast-header strong');
    
    toastBody.textContent = message;
    toast.className = `toast bg-${type === 'danger' ? 'danger' : type === 'success' ? 'success' : 'info'} text-white`;
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

// ==================== Authentication Functions ====================

// Check authentication status
async function checkAuthStatus() {
    try {
        const response = await apiFetch('/api/auth/profile/');
        if (response.status === 200) {
            updateUIForLoggedInUser(response.data);
        }
    } catch (error) {
        updateUIForLoggedOutUser();
    }
}

// Handle login
async function handleLogin() {
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    if (!username || !password) {
        showToast('Please enter username and password', 'warning');
        return;
    }
    
    try {
        const response = await apiFetch('/api/auth/login/', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        
        if (response.status === 200) {
            showToast('Login successful!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('loginModal')).hide();
            updateUIForLoggedInUser(response.data.user);
            loadBookings();
            
            // Clear form
            document.getElementById('loginForm').reset();
        }
    } catch (error) {
        // Error already shown by apiFetch
    }
}

// Handle signup
async function handleSignup() {
    const username = document.getElementById('signupUsername').value;
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;
    const passwordConfirm = document.getElementById('signupPasswordConfirm').value;
    
    if (!username || !email || !password || !passwordConfirm) {
        showToast('Please fill all fields', 'warning');
        return;
    }
    
    if (password !== passwordConfirm) {
        showToast('Passwords do not match', 'warning');
        return;
    }
    
    if (password.length < 8) {
        showToast('Password must be at least 8 characters', 'warning');
        return;
    }
    
    try {
        const response = await apiFetch('/api/auth/signup/', {
            method: 'POST',
            body: JSON.stringify({
                username,
                email,
                password,
                password_confirm: passwordConfirm
            })
        });
        
        if (response.status === 201) {
            showToast('Account created successfully!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('signupModal')).hide();
            updateUIForLoggedInUser(response.data.user);
            loadBookings();
            
            // Clear form
            document.getElementById('signupForm').reset();
        }
    } catch (error) {
        // Error already shown by apiFetch
    }
}

// Handle logout
async function handleLogout() {
    try {
        const response = await apiFetch('/api/auth/logout/', {
            method: 'POST'
        });
        
        if (response.status === 200) {
            showToast('Logged out successfully', 'success');
            updateUIForLoggedOutUser();
            loadBookings();
        }
    } catch (error) {
        // Even if error, update UI
        updateUIForLoggedOutUser();
    }
}

// Update UI for logged in user
function updateUIForLoggedInUser(userData) {
    currentUser = userData;
    
    // Hide login/signup buttons
    document.getElementById('loginNavBtn').parentElement.classList.add('d-none');
    document.getElementById('signupNavBtn').parentElement.classList.add('d-none');
    
    // Show user info
    const userNavItem = document.getElementById('userNavItem');
    userNavItem.classList.remove('d-none');
    document.getElementById('userNameNav').textContent = userData.username;
}

// Update UI for logged out user
function updateUIForLoggedOutUser() {
    currentUser = null;
    
    // Show login/signup buttons
    document.getElementById('loginNavBtn').parentElement.classList.remove('d-none');
    document.getElementById('signupNavBtn').parentElement.classList.remove('d-none');
    
    // Hide user info
    document.getElementById('userNavItem').classList.add('d-none');
}

