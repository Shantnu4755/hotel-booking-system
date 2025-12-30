"""URL configuration for the bookings app.

All routes use class-based views with GET and POST methods only.
"""

from __future__ import annotations

from django.urls import path
from . import views

app_name = "bookings"

urlpatterns = [
    # Authentication endpoints
    path("auth/signup/", views.SignupView.as_view(), name="signup"),
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("auth/profile/", views.UserProfileView.as_view(), name="user-profile"),
    
    # Room endpoints
    path("rooms/", views.RoomListView.as_view(), name="room-list"),
    path("rooms/<int:pk>/", views.RoomDetailView.as_view(), name="room-detail"),
    path("rooms/available/", views.RoomAvailableView.as_view(), name="room-available"),
    
    # Booking endpoints
    path("bookings/", views.BookingListView.as_view(), name="booking-list"),
    path("bookings/<int:pk>/", views.BookingDetailView.as_view(), name="booking-detail"),
    path("bookings/<int:pk>/check-in/", views.BookingCheckInView.as_view(), name="booking-check-in"),
    path("bookings/<int:pk>/check-out/", views.BookingCheckOutView.as_view(), name="booking-check-out"),
    path("bookings/<int:pk>/cancel/", views.BookingCancelView.as_view(), name="booking-cancel"),
]
