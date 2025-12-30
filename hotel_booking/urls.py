from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from bookings.views import frontend_view

urlpatterns = [
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/', include('bookings.urls', namespace='bookings')),

    # JWT authentication endpoints
    path('api/auth/jwt/create/', TokenObtainPairView.as_view(), name='jwt-create'),
    path('api/auth/jwt/refresh/', TokenRefreshView.as_view(), name='jwt-refresh'),

    # Frontend home page
    path('', frontend_view, name='frontend'),
]
