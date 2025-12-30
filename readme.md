# 🏨 Hotel Room Booking System

A full-stack hotel room booking application built with **Django + Django REST Framework** and a **modern vanilla JS + Bootstrap frontend**.

The system allows **public users to browse rooms**, **authenticated users to book rooms**, and enforces **strong business rules** such as overlap prevention, lifecycle transitions, and secure authentication.

---

## 📌 Features Overview

- 🔓 Public room browsing (no login required)
- 🔐 Secure authentication (Signup, Login, Logout)
- 🏨 Real-time room availability search
- 📅 Hourly & Daily booking support
- 💰 Accurate price calculation with ceiling logic
- 🚫 Prevents overlapping bookings
- 🔄 Booking lifecycle (Confirm → Check-in → Check-out → Cancel)
- 🧠 Clean separation of concerns (Models, Services, Views)
- 🎨 Premium hotel-style UI

---

## 🏗️ High-Level Architecture

```
Frontend (HTML + CSS + JS)
        ↓
Django REST API
        ↓
Service Layer (Business Logic)
        ↓
Django ORM (Models)
        ↓
Database
```

---

## 📂 Project Structure

```
bookings/
├── models.py          # Core domain models
├── services.py        # Business logic
├── serializers.py     # API validation
├── views.py           # API endpoints
├── urls.py            # Routes
├── admin.py           # Admin panel
├── tests.py           # Automated tests

static/
├── css/style.css
├── js/app.js

templates/
├── frontend.html
```

---

## 🔐 Authentication Flow

### Signup
- `POST /api/auth/signup/`
- Creates user
- Auto login using session auth

### Login
- `POST /api/auth/login/`
- Creates authenticated session

### Logout
- `POST /api/auth/logout/`
- Clears session and cache

### Profile Check
- `GET /api/auth/profile/`
- Used by frontend to detect login state

---

## 🛡️ Permissions & Decorators

| Permission | Usage |
|---------|------|
| AllowAny | Public room browsing |
| IsAuthenticated | Booking operations |
| IsOwner | Booking ownership check |

All API views are wrapped using:

```python
@method_decorator(csrf_exempt, name='dispatch')
```

---

## 🏨 Public Room Browsing (No Login Required)

Endpoints:
- `GET /api/rooms/`
- `GET /api/rooms/{id}/`
- `GET /api/rooms/available/`

Flow:
1. User searches dates
2. Backend excludes overlapping bookings
3. Available rooms returned
4. Displayed on UI

---

## 📅 Booking Flow (Login Required)

1. User selects room
2. Clicks Book Now
3. If not logged in → Login / Signup modal
4. Booking request sent
5. Backend validates & creates booking

---

## 🧠 Business Logic (Service Layer)

### Pricing Rules
- Hourly: `ceil(hours) × base_price_per_hour`
- Daily: `ceil(days) × base_price_per_day`

### Overlap Prevention
```
start < existing_end AND end > existing_start
```

All booking creation uses atomic transactions to avoid race conditions.

---

## 🔄 Booking Lifecycle

```
CONFIRMED → CHECKED_IN → COMPLETED
        ↘
         CANCELED
```

Endpoints:
- `/check-in/`
- `/check-out/`
- `/cancel/`

---

## 🎨 Frontend Responsibilities

- Room search & display
- Authentication UI handling
- Price estimation
- Booking actions
- Toast notifications

---

## 🧪 Testing

- Overlapping booking prevention
- Price rounding logic
- Booking lifecycle transitions
- Cancel rules

Tests are API-level for full coverage.

---

## 🛠️ Admin Panel

- Room management
- Booking visibility
- Filters & search
- Read-only timestamps

---

## 🚀 Design Principles

- Separation of concerns
- Domain-driven services
- Transaction safety
- Scalable architecture

---

## 👨‍💻 Author

**Shantnu Kadam**  
Backend Developer (Python / Django)

---

## 📌 Future Enhancements

- Image uploads
- Payment gateway
- Email notifications
- Coupons & discounts
- Pagination
